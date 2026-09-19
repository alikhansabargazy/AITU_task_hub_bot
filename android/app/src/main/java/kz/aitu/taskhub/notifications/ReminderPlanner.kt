package kz.aitu.taskhub.notifications

import kz.aitu.taskhub.data.LessonDto
import kz.aitu.taskhub.data.ProfileDto
import kz.aitu.taskhub.ui.Msg
import java.time.Instant
import java.time.LocalTime
import java.time.ZoneId
import java.time.temporal.WeekFields

data class ReminderEvent(val key: String, val at: Long, val until: Long, val title: String, val text: String)

object ReminderPlanner {
    fun events(profile: ProfileDto, lessons: List<LessonDto>, now: Instant): List<ReminderEvent> {
        if (!profile.notificationsEnabled) return emptyList()
        val zone = runCatching { ZoneId.of(profile.timezone) }.getOrElse { ZoneId.of("UTC") }
        val today = now.atZone(zone).toLocalDate()
        return (0..14).flatMap { offset ->
            val day = today.plusDays(offset.toLong())
            val parity = if ((day.get(WeekFields.ISO.weekOfWeekBasedYear()) + profile.weekParityOffset) % 2 == 1) "numerator" else "denominator"
            lessons.filter { it.dayOfWeek == day.dayOfWeek.value && (it.parity == "all" || it.parity == parity) }.mapNotNull { lesson ->
                runCatching {
                    val start = day.atTime(LocalTime.parse(lesson.startTime)).atZone(zone)
                    var end = day.atTime(LocalTime.parse(lesson.endTime)).atZone(zone)
                    if (end < start) end = end.plusDays(1)
                    val at = start.minusMinutes(profile.reminderMinutes.toLong()).toInstant()
                    if (!at.isAfter(now)) return@mapNotNull null
                    ReminderEvent(
                        "${profile.userId}:${lesson.id}:$day:${profile.reminderMinutes}", at.toEpochMilli(), end.toInstant().toEpochMilli(),
                        (if (profile.reminderMinutes == 0) Msg.CLASS_NOW else Msg.CLASS_REMINDER).text(profile.language),
                        listOfNotNull(lesson.subject, "${lesson.startTime.take(5)}–${lesson.endTime.take(5)}", lesson.location, lesson.teacher).joinToString(" · "),
                    )
                }.getOrNull()
            }
        }.sortedBy { it.at }.take(400)
    }
}
