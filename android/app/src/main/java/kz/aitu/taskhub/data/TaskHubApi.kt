package kz.aitu.taskhub.data

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface TaskHubApi {
    @GET("api/v1/users/{userId}/tasks")
    suspend fun getTasks(
        @Path("userId") userId: Long,
        @Query("completed") completed: Boolean? = null,
    ): List<TaskDto>

    @POST("api/v1/users/{userId}/tasks")
    suspend fun createTask(
        @Path("userId") userId: Long,
        @Body request: CreateTaskRequest,
    ): TaskDto

    @PATCH("api/v1/users/{userId}/tasks/{taskId}")
    suspend fun updateTask(
        @Path("userId") userId: Long,
        @Path("taskId") taskId: Long,
        @Body request: UpdateTaskRequest,
    ): TaskDto

    @DELETE("api/v1/users/{userId}/tasks/{taskId}")
    suspend fun deleteTask(
        @Path("userId") userId: Long,
        @Path("taskId") taskId: Long,
    ): Response<Unit>
}
