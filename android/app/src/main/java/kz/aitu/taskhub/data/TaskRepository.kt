package kz.aitu.taskhub.data

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope

class TaskRepository(val api: TaskHubApi) {
    suspend fun snapshot(): Snapshot = coroutineScope {
        val profile = async { api.profile() }
        val tasks = async { api.tasks() }
        val lessons = async { api.lessons() }
        val dashboard = async { api.dashboard() }
        Snapshot(profile.await(), tasks.await(), lessons.await(), dashboard.await())
    }
}
