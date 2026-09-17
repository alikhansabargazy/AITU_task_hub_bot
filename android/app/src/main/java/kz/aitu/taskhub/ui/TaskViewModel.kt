package kz.aitu.taskhub.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kz.aitu.taskhub.data.TaskDto
import kz.aitu.taskhub.data.TaskHubNetwork
import kz.aitu.taskhub.data.TaskRepository
import retrofit2.HttpException

enum class TaskFilter {
    ALL,
    ACTIVE,
    COMPLETED,
}

data class TaskUiState(
    val tasks: List<TaskDto> = emptyList(),
    val filter: TaskFilter = TaskFilter.ACTIVE,
    val isLoading: Boolean = true,
    val isWorking: Boolean = false,
    val error: String? = null,
) {
    val visibleTasks: List<TaskDto>
        get() = when (filter) {
            TaskFilter.ALL -> tasks
            TaskFilter.ACTIVE -> tasks.filterNot(TaskDto::isCompleted)
            TaskFilter.COMPLETED -> tasks.filter(TaskDto::isCompleted)
        }
}

class TaskViewModel(
    private val repository: TaskRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(TaskUiState())
    val uiState: StateFlow<TaskUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun setFilter(filter: TaskFilter) {
        _uiState.update { it.copy(filter = filter) }
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            try {
                val tasks = repository.tasks()
                _uiState.update { it.copy(tasks = tasks, isLoading = false) }
            } catch (error: Throwable) {
                _uiState.update {
                    it.copy(isLoading = false, error = error.userMessage())
                }
            }
        }
    }

    fun createTask(text: String) {
        if (text.isBlank()) return
        mutate {
            val created = repository.create(text)
            _uiState.update { state ->
                state.copy(tasks = listOf(created) + state.tasks)
            }
        }
    }

    fun setCompleted(task: TaskDto, completed: Boolean) {
        mutate {
            val updated = repository.setCompleted(task, completed)
            _uiState.update { state ->
                state.copy(
                    tasks = state.tasks.map { current ->
                        if (current.id == updated.id) updated else current
                    },
                )
            }
        }
    }

    fun deleteTask(task: TaskDto) {
        mutate {
            repository.delete(task)
            _uiState.update { state ->
                state.copy(tasks = state.tasks.filterNot { it.id == task.id })
            }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }

    private fun mutate(action: suspend () -> Unit) {
        viewModelScope.launch {
            _uiState.update { it.copy(isWorking = true, error = null) }
            try {
                action()
            } catch (error: Throwable) {
                _uiState.update { it.copy(error = error.userMessage()) }
            } finally {
                _uiState.update { it.copy(isWorking = false) }
            }
        }
    }

    private fun Throwable.userMessage(): String = when (this) {
        is HttpException -> "Сервер вернул ошибку ${code()}"
        else -> localizedMessage ?: "Не удалось связаться с сервером"
    }

    companion object {
        private const val DEMO_USER_ID = 1L

        val Factory: ViewModelProvider.Factory = viewModelFactory {
            initializer {
                TaskViewModel(
                    repository = TaskRepository(
                        api = TaskHubNetwork.api,
                        userId = DEMO_USER_ID,
                    ),
                )
            }
        }
    }
}
