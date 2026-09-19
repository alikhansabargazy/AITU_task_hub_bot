package kz.aitu.taskhub.data

import com.google.gson.JsonObject
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path

interface TaskHubApi {
    @POST("api/v1/auth/register") suspend fun register(@Body body: JsonObject): SessionDto
    @POST("api/v1/auth/login") suspend fun login(@Body body: JsonObject): SessionDto
    @POST("api/v1/auth/logout") suspend fun logout()
    @PATCH("api/v1/auth/password") suspend fun changePassword(@Body body: JsonObject): SessionDto
    @GET("api/v1/me") suspend fun profile(): ProfileDto
    @PATCH("api/v1/me/settings") suspend fun updateSettings(@Body body: JsonObject): JsonObject
    @GET("api/v1/me/dashboard") suspend fun dashboard(): DashboardDto
    @GET("api/v1/me/tasks") suspend fun tasks(): List<TaskDto>
    @POST("api/v1/me/tasks") suspend fun createTask(@Body body: TaskInput): TaskDto
    @PATCH("api/v1/me/tasks/{id}") suspend fun updateTask(@Path("id") id: Long, @Body body: JsonObject): TaskDto
    @DELETE("api/v1/me/tasks/{id}") suspend fun deleteTask(@Path("id") id: Long)
    @GET("api/v1/me/schedule") suspend fun lessons(): List<LessonDto>
    @POST("api/v1/me/schedule") suspend fun createLesson(@Body body: LessonInput): LessonDto
    @PATCH("api/v1/me/schedule/{id}") suspend fun updateLesson(@Path("id") id: Long, @Body body: LessonInput): LessonDto
    @DELETE("api/v1/me/schedule/{id}") suspend fun deleteLesson(@Path("id") id: Long)
}
