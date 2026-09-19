package kz.aitu.taskhub

import kz.aitu.taskhub.data.*
import kz.aitu.taskhub.notifications.ReminderPlanner
import org.junit.Assert.*
import org.junit.Test
import java.time.Instant

class ReminderPlannerTest {
    private val profile = ProfileDto(-1, "alikhan", "Alikhan", "UTC", "en", true, 15, 0, 7)
    private val lesson = LessonDto(1, -1, "Math", 1, "09:00:00", "09:50:00", "all", "Lab", "C1", "Ada")

    @Test fun calculatesReminderAndPreservesUserText() {
        val events = ReminderPlanner.events(profile, listOf(lesson), Instant.parse("2026-09-21T08:00:00Z"))
        assertEquals(Instant.parse("2026-09-21T08:45:00Z").toEpochMilli(), events.first().at)
        assertTrue(events.first().text.contains("Math"))
        assertTrue(events.first().text.contains("Ada"))
    }

    @Test fun zeroMeansAtStartAndDisabledMeansNoReminders() {
        val now = Instant.parse("2026-09-21T08:00:00Z")
        assertEquals(Instant.parse("2026-09-21T09:00:00Z").toEpochMilli(), ReminderPlanner.events(profile.copy(reminderMinutes = 0), listOf(lesson), now).first().at)
        assertTrue(ReminderPlanner.events(profile.copy(notificationsEnabled = false), listOf(lesson), now).isEmpty())
    }

    @Test fun reminderCanFallOnPreviousLocalDate() {
        val monday = lesson.copy(startTime = "00:05:00", endTime = "01:00:00")
        val events = ReminderPlanner.events(profile, listOf(monday), Instant.parse("2026-09-20T23:00:00Z"))
        assertEquals(Instant.parse("2026-09-20T23:50:00Z").toEpochMilli(), events.first().at)
    }

    @Test fun parityUsesIsoWeekAcrossNewYearAndOffset() {
        // 2027-01-01 belongs to ISO week 53 of 2026, not week 1 of 2027.
        val friday = lesson.copy(dayOfWeek = 5, parity = "numerator")
        val now = Instant.parse("2027-01-01T08:00:00Z")
        assertEquals(Instant.parse("2027-01-01T08:45:00Z").toEpochMilli(), ReminderPlanner.events(profile, listOf(friday), now).first().at)
        // Week 53 is followed by week 1: both are odd. With the offset,
        // the next matching Friday is in week 2, on January 15.
        assertEquals(Instant.parse("2027-01-15T08:45:00Z").toEpochMilli(), ReminderPlanner.events(profile.copy(weekParityOffset = 1), listOf(friday), now).first().at)
    }

    @Test fun timezoneIsTheProfileZoneNotTheDeviceZone() {
        val zoned = profile.copy(timezone = "Asia/Almaty")
        val events = ReminderPlanner.events(zoned, listOf(lesson), Instant.parse("2026-09-21T03:00:00Z"))
        assertEquals(Instant.parse("2026-09-21T03:45:00Z").toEpochMilli(), events.first().at)
    }

    @Test fun pastEventsAreNotReplayed() {
        val now = Instant.parse("2026-09-21T10:00:00Z")
        val events = ReminderPlanner.events(profile, listOf(lesson), now)
        assertTrue(events.all { it.at > now.toEpochMilli() })
        assertEquals(events.size, events.map { it.key }.toSet().size)
    }
}
