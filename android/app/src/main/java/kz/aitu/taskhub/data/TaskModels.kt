package kz.aitu.taskhub.data

import com.google.gson.annotations.SerializedName

data class TaskDto(
    val id: Long,
    @SerializedName("user_id") val userId: Long,
    val text: String,
    @SerializedName("subject_name") val subjectName: String?,
    val deadline: String?,
    val priority: String,
    @SerializedName("is_completed") val isCompleted: Boolean,
)

data class CreateTaskRequest(
    val text: String,
    @SerializedName("subject_name") val subjectName: String? = null,
    val deadline: String? = null,
    val priority: String = "normal",
)

data class UpdateTaskRequest(
    @SerializedName("is_completed") val isCompleted: Boolean,
)
