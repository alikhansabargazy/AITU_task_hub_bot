package kz.aitu.taskhub

import kz.aitu.taskhub.data.*
import kz.aitu.taskhub.ui.Msg
import org.junit.Assert.*
import org.junit.Test

class SerializationTest {
    @Test fun editingExplicitlyClearsOptionalFieldsWithoutChangingCompletion() {
        val task = TaskHubNetwork.gson.toJsonTree(TaskInput("Updated", null, null, "normal")).asJsonObject
        assertTrue(task["deadline"].isJsonNull)
        assertTrue(task["subject_name"].isJsonNull)
        assertFalse(task.has("is_completed"))
        val lesson = TaskHubNetwork.gson.toJsonTree(LessonInput("Math", 1, "09:00", "10:00", "all", null, null, null)).asJsonObject
        assertTrue(lesson["teacher"].isJsonNull)
        assertTrue(lesson["location"].isJsonNull)
    }

    @Test fun allUiLabelsHaveAllThreeLanguages() {
        Msg.entries.forEach { label ->
            listOf("ru", "en", "kk").forEach { language -> assertTrue(label.text(language).isNotBlank()) }
        }
    }

    @Test fun normalizesServerUrlAndRejectsEmbeddedCredentials() {
        assertEquals("http://192.168.10.4:8000/", TaskHubNetwork.normalizeUrl(" http://192.168.10.4:8000 "))
        assertThrows(IllegalArgumentException::class.java) { TaskHubNetwork.normalizeUrl("https://username:password@example.com/") }
    }
}
