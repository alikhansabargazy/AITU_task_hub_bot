package kz.aitu.taskhub.data

class TaskRepository(
    private val api: TaskHubApi,
    private val userId: Long,
) {
    suspend fun tasks(): List<TaskDto> = api.getTasks(userId)

    suspend fun create(text: String): TaskDto =
        api.createTask(userId, CreateTaskRequest(text = text.trim()))

    suspend fun setCompleted(task: TaskDto, completed: Boolean): TaskDto =
        api.updateTask(userId, task.id, UpdateTaskRequest(isCompleted = completed))

    suspend fun delete(task: TaskDto) {
        val response = api.deleteTask(userId, task.id)
        check(response.isSuccessful) { "Не удалось удалить задачу (${response.code()})" }
    }
}
