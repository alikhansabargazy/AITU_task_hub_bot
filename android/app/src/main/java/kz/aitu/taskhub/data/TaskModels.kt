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

data class TaskInput(
    val text: String,
    @SerializedName("subject_name") val subjectName: String?,
    val deadline: String?,
    val priority: String,
)

data class LessonDto(
    val id: Long,
    @SerializedName("user_id") val userId: Long,
    val subject: String,
    @SerializedName("day_of_week") val dayOfWeek: Int,
    @SerializedName("start_time") val startTime: String,
    @SerializedName("end_time") val endTime: String,
    val parity: String,
    @SerializedName("lesson_type") val lessonType: String?,
    val location: String?,
    val teacher: String?,
)

data class LessonInput(
    val subject: String,
    @SerializedName("day_of_week") val dayOfWeek: Int,
    @SerializedName("start_time") val startTime: String,
    @SerializedName("end_time") val endTime: String,
    val parity: String,
    @SerializedName("lesson_type") val lessonType: String?,
    val location: String?,
    val teacher: String?,
)

data class ProfileDto(
    @SerializedName("user_id") val userId: Long,
    val username: String,
    @SerializedName("display_name") val displayName: String,
    val timezone: String,
    val language: String,
    @SerializedName("notifications_enabled") val notificationsEnabled: Boolean,
    @SerializedName("reminder_minutes") val reminderMinutes: Int,
    @SerializedName("week_parity_offset") val weekParityOffset: Int,
    @SerializedName("dashboard_days") val dashboardDays: Int,
)

data class LessonOccurrence(val start: String, val end: String, val lesson: LessonDto)

data class DashboardDto(
    @SerializedName("local_now") val localNow: String,
    val timezone: String,
    @SerializedName("iso_week") val isoWeek: Int,
    val parity: String,
    @SerializedName("dashboard_days") val dashboardDays: Int,
    @SerializedName("today_count") val todayCount: Int,
    @SerializedName("active_count") val activeCount: Int,
    @SerializedName("later_count") val laterCount: Int,
    @SerializedName("current_lessons") val currentLessons: List<LessonOccurrence>,
    @SerializedName("next_lesson") val nextLesson: LessonOccurrence?,
    val overdue: List<TaskDto>,
    val upcoming: List<TaskDto>,
    val undated: List<TaskDto>,
)

data class SessionDto(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("expires_at") val expiresAt: String,
)

data class Snapshot(
    val profile: ProfileDto,
    val tasks: List<TaskDto>,
    val lessons: List<LessonDto>,
    val dashboard: DashboardDto,
)
