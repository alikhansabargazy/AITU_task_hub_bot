package kz.aitu.taskhub.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kz.aitu.taskhub.data.*
import kz.aitu.taskhub.notifications.ReminderScheduler
import kz.aitu.taskhub.notifications.SyncWorker
import retrofit2.HttpException
import java.io.IOException

enum class TaskFilter { ALL, ACTIVE, COMPLETED }

data class TaskUiState(
    val authenticated: Boolean = false,
    val baseUrl: String = "",
    val language: String = "ru",
    val snapshot: Snapshot? = null,
    val filter: TaskFilter = TaskFilter.ACTIVE,
    val search: String = "",
    val isLoading: Boolean = false,
    val isWorking: Boolean = false,
    val offline: Boolean = false,
    val error: String? = null,
    val notice: String? = null,
) {
    val visibleTasks: List<TaskDto>
        get() = snapshot?.tasks.orEmpty().filter {
            (filter == TaskFilter.ALL || it.isCompleted == (filter == TaskFilter.COMPLETED)) &&
                (search.isBlank() || it.text.contains(search, true) || it.subjectName.orEmpty().contains(search, true))
        }
}

class TaskViewModel(application: Application) : AndroidViewModel(application) {
    private val store = SessionStore(application)
    private var repository: TaskRepository? = null
    private val _uiState = MutableStateFlow(TaskUiState(
        authenticated = store.token != null, baseUrl = store.baseUrl,
        language = store.language, snapshot = store.cachedSnapshot(),
    ))
    val uiState = _uiState.asStateFlow()

    init {
        if (store.token != null) {
            SyncWorker.schedule(application)
            ReminderScheduler.reschedule(application)
            refresh()
        } else {
            ReminderScheduler.cancelAll(application)
        }
    }

    private fun repo(): TaskRepository = repository ?: TaskRepository(
        TaskHubNetwork.api(store.baseUrl, store.token),
    ).also { repository = it }

    fun setFilter(filter: TaskFilter) { _uiState.update { it.copy(filter = filter) } }
    fun setSearch(search: String) { _uiState.update { it.copy(search = search) } }
    fun clearError() { _uiState.update { it.copy(error = null, notice = null) } }
    fun setLoginLanguage(code: String) {
        store.setLanguage(code)
        _uiState.update { it.copy(language = code) }
    }

    fun authenticate(url: String, username: String, password: String, name: String, register: Boolean) {
        if (_uiState.value.isWorking) return
        val normalized = try { TaskHubNetwork.normalizeUrl(url) } catch (_: IllegalArgumentException) {
            _uiState.update { it.copy(error = Msg.INVALID_URL.text(it.language)) }
            return
        }
        _uiState.update { it.copy(isWorking = true, error = null) }
        viewModelScope.launch {
            try {
                store.setBaseUrl(normalized)
                val api = TaskHubNetwork.api(normalized, null)
                val payload = JsonObject().apply {
                    addProperty("username", username.trim().lowercase())
                    addProperty("password", password)
                    if (register) {
                        addProperty("display_name", name.trim().ifBlank { username.trim() })
                        addProperty("language", _uiState.value.language)
                    }
                }
                val session = if (register) api.register(payload) else api.login(payload)
                store.saveSession(session)
                repository = null
                _uiState.update { it.copy(authenticated = true, baseUrl = normalized, snapshot = null) }
                SyncWorker.schedule(getApplication<Application>())
                loadSnapshot()
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                _uiState.update { it.copy(error = message(error, authenticating = !it.authenticated)) }
            } finally {
                _uiState.update { it.copy(isWorking = false) }
            }
        }
    }

    fun refresh() {
        if (!_uiState.value.authenticated || _uiState.value.isWorking || _uiState.value.isLoading) return
        _uiState.update { it.copy(isLoading = true) }
        viewModelScope.launch {
            try {
                loadSnapshot()
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                handleError(error)
            } finally {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }

    private suspend fun loadSnapshot() {
        val expectedToken = store.token
        if (expectedToken == null) {
            clearSession()
            _uiState.update { it.copy(error = Msg.SESSION_EXPIRED.text(it.language)) }
            return
        }
        val expectedUrl = store.baseUrl
        val snapshot = repo().snapshot()
        if (store.saveSnapshot(snapshot, expectedToken, expectedUrl)) {
            _uiState.update { it.copy(snapshot = snapshot, language = snapshot.profile.language, offline = false, error = null) }
            ReminderScheduler.reschedule(getApplication<Application>())
        }
    }

    private fun mutate(onSuccess: () -> Unit = {}, action: suspend () -> Unit) {
        if (_uiState.value.isWorking || _uiState.value.isLoading) return
        _uiState.update { it.copy(isWorking = true, error = null, notice = null) }
        viewModelScope.launch {
            try {
                store.markChanged()
                action()
                store.markChanged()
                // Close a successful editor even if the following refresh fails: avoid duplicate creates.
                onSuccess()
                loadSnapshot()
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                handleError(error)
            } finally {
                _uiState.update { it.copy(isWorking = false) }
            }
        }
    }

    fun saveTask(existing: TaskDto?, input: TaskInput, onSuccess: () -> Unit) = mutate(onSuccess) {
        if (existing == null) repo().api.createTask(input)
        else repo().api.updateTask(existing.id, TaskHubNetwork.gson.toJsonTree(input).asJsonObject)
    }

    fun setCompleted(task: TaskDto, completed: Boolean) = mutate {
        repo().api.updateTask(task.id, JsonObject().apply { addProperty("is_completed", completed) })
    }

    fun deleteTask(task: TaskDto, onSuccess: () -> Unit) = mutate(onSuccess) { repo().api.deleteTask(task.id) }

    fun saveLesson(existing: LessonDto?, input: LessonInput, onSuccess: () -> Unit) = mutate(onSuccess) {
        if (existing == null) repo().api.createLesson(input) else repo().api.updateLesson(existing.id, input)
    }

    fun deleteLesson(lesson: LessonDto, onSuccess: () -> Unit) = mutate(onSuccess) { repo().api.deleteLesson(lesson.id) }

    fun updateSettings(body: JsonObject, onSuccess: () -> Unit = {}) = mutate(onSuccess) { repo().api.updateSettings(body) }

    fun logout() {
        if (_uiState.value.isWorking || _uiState.value.isLoading) return
        _uiState.update { it.copy(isWorking = true) }
        viewModelScope.launch {
            var failure: String? = null
            try {
                repo().api.logout()
            } catch (error: CancellationException) {
                throw error
            } catch (_: Exception) {
                failure = when (store.language) {
                    "en" -> "Signed out on this phone. The offline server could not revoke the session; it expires within 30 days."
                    "kk" -> "Осы телефоннан шықтыңыз. Сервер сессияны жоя алмады; ол 30 күн ішінде аяқталады."
                    else -> "На телефоне выполнен выход. Недоступный сервер не смог отозвать сессию; она истечёт в течение 30 дней."
                }
            } finally {
                clearSession()
                _uiState.update { it.copy(notice = failure) }
            }
        }
    }

    fun changePassword(old: String, new: String, onSuccess: () -> Unit) {
        if (_uiState.value.isWorking || _uiState.value.isLoading) return
        _uiState.update { it.copy(isWorking = true, error = null) }
        viewModelScope.launch {
            try {
                val result = repo().api.changePassword(JsonObject().apply {
                    addProperty("current_password", old)
                    addProperty("new_password", new)
                })
                store.saveSession(result)
                repository = null
                onSuccess()
                _uiState.update { it.copy(notice = Msg.PASSWORD_CHANGED.text(it.language)) }
                loadSnapshot()
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                _uiState.update { it.copy(error = message(error, authenticating = true)) }
            } finally {
                _uiState.update { it.copy(isWorking = false) }
            }
        }
    }

    private fun clearSession() {
        store.clearSession()
        repository = null
        SyncWorker.cancel(getApplication<Application>())
        ReminderScheduler.cancelAll(getApplication<Application>())
        _uiState.value = TaskUiState(baseUrl = store.baseUrl, language = store.language)
    }

    private fun handleError(error: Exception) {
        if (error is HttpException && error.code() == 401) {
            clearSession()
            _uiState.update { it.copy(error = Msg.SESSION_EXPIRED.text(it.language)) }
        } else {
            _uiState.update { it.copy(offline = error is IOException, error = message(error)) }
        }
    }

    private fun message(error: Exception, authenticating: Boolean = false): String {
        val labels = Labels(_uiState.value.language)
        if (error is IOException) return labels[Msg.NETWORK_ERROR]
        if (error is HttpException) {
            if (error.code() == 401 && authenticating) return labels[Msg.AUTH_ERROR]
            if (error.code() == 409 && authenticating) return labels[Msg.USERNAME_TAKEN]
            if (error.code() == 429) return labels[Msg.RATE_LIMIT]
            val detail = runCatching {
                val value = JsonParser.parseString(error.response()?.errorBody()?.string()).asJsonObject["detail"]
                if (value.isJsonPrimitive) value.asString else value.asJsonArray.joinToString("\n") {
                    val item = it.asJsonObject
                    item["loc"].asJsonArray.joinToString(".") { part -> part.asString } + ": " + item["msg"].asString
                }
            }.getOrNull()
            return detail ?: labels[Msg.SERVER_ERROR, error.code()]
        }
        return labels[Msg.INVALID_FORM]
    }
}
