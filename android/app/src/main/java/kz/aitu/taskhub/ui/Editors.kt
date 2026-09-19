package kz.aitu.taskhub.ui

import android.app.DatePickerDialog
import android.app.TimePickerDialog
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import kz.aitu.taskhub.data.*
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.format.DateTimeFormatter

@Composable
fun EditorDialog(title: String, busy: Boolean, error: String?, onDismiss: () -> Unit, onSave: () -> Unit, content: @Composable ColumnScope.() -> Unit) {
    val s = LocalLabels.current
    Dialog(onDismissRequest = { if (!busy) onDismiss() }, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(Modifier.fillMaxWidth(0.94f).fillMaxHeight(0.9f).imePadding(), shape = MaterialTheme.shapes.extraLarge) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                SectionTitle(title)
                if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                Column(Modifier.weight(1f).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    error?.let { Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
                    content()
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                    TextButton(onClick = onDismiss, enabled = !busy) { Text(s[Msg.CANCEL]) }
                    Button(onClick = onSave, enabled = !busy) { Text(s[if (busy) Msg.WORKING else Msg.SAVE]) }
                }
            }
        }
    }
}

@Composable
fun Input(value: String, onChange: (String) -> Unit, label: String, limit: Int, enabled: Boolean = true, multiline: Boolean = false) {
    OutlinedTextField(value, { onChange(it.take(limit)) }, Modifier.fillMaxWidth(), label = { Text(label) }, enabled = enabled,
        singleLine = !multiline, minLines = if (multiline) 2 else 1)
}

@Composable
private fun TimeInput(value: String, onChange: (String) -> Unit, label: String, enabled: Boolean) {
    val context = LocalContext.current
    val s = LocalLabels.current
    Row(verticalAlignment = Alignment.CenterVertically) {
        OutlinedTextField(value, { onChange(it.take(5)) }, Modifier.weight(1f), label = { Text(label + " · HH:mm") }, singleLine = true, enabled = enabled)
        TextButton(enabled = enabled, onClick = {
            val time = runCatching { LocalTime.parse(value) }.getOrDefault(LocalTime.of(9, 0))
            TimePickerDialog(context, { _, hour, minute -> onChange(LocalTime.of(hour, minute).format(DateTimeFormatter.ofPattern("HH:mm"))) }, time.hour, time.minute, true).show()
        }) { Text(s[Msg.TIME]) }
    }
}

@Composable
fun TaskEditor(task: TaskDto?, busy: Boolean, serverError: String?, onDismiss: () -> Unit, onSave: (TaskInput) -> Unit) {
    val s = LocalLabels.current
    val context = LocalContext.current
    var text by rememberSaveable(task?.id) { mutableStateOf(task?.text.orEmpty()) }
    var subject by rememberSaveable(task?.id) { mutableStateOf(task?.subjectName.orEmpty()) }
    var priority by rememberSaveable(task?.id) { mutableStateOf(task?.priority ?: "normal") }
    var hasDeadline by rememberSaveable(task?.id) { mutableStateOf(task?.deadline != null) }
    var date by rememberSaveable(task?.id) { mutableStateOf(task?.deadline?.substringBefore('T') ?: LocalDate.now().toString()) }
    var time by rememberSaveable(task?.id) { mutableStateOf(task?.deadline?.substringAfter('T')?.take(5) ?: "18:00") }
    var error by rememberSaveable { mutableStateOf<String?>(null) }
    EditorDialog(s[if (task == null) Msg.ADD_TASK else Msg.EDIT], busy, error ?: serverError, onDismiss, {
        if (text.isBlank()) error = s[Msg.INVALID_FORM]
        else {
            val deadline = if (hasDeadline) runCatching { LocalDateTime.of(LocalDate.parse(date), LocalTime.parse(time)).toString() }.getOrNull() else null
            if (hasDeadline && deadline == null) error = s[Msg.INVALID_DATE]
            else { error = null; onSave(TaskInput(text.trim(), subject.trim().ifEmpty { null }, deadline, priority)) }
        }
    }) {
        Input(text, { text = it; error = null }, s[Msg.TASK_TITLE], 255, !busy, multiline = true)
        Input(subject, { subject = it }, s[Msg.SUBJECT] + " · " + s[Msg.OPTIONAL], 100, !busy)
        SectionTitle(s[Msg.PRIORITY])
        ChoiceRow(listOf("normal" to s[Msg.NORMAL], "high" to s[Msg.HIGH]), priority, { priority = it }, !busy)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(hasDeadline, { hasDeadline = it }, enabled = !busy)
            Text(s[Msg.DEADLINE])
        }
        if (hasDeadline) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(date, { date = it.take(10) }, Modifier.weight(1f), label = { Text("YYYY-MM-DD") }, singleLine = true, enabled = !busy)
                TextButton(enabled = !busy, onClick = {
                    val day = runCatching { LocalDate.parse(date) }.getOrDefault(LocalDate.now())
                    DatePickerDialog(context, { _, year, month, chosen -> date = LocalDate.of(year, month + 1, chosen).toString() }, day.year, day.monthValue - 1, day.dayOfMonth).show()
                }) { Text(s[Msg.DATE]) }
            }
            TimeInput(time, { time = it }, s[Msg.TIME], !busy)
        }
    }
}

@Composable
fun LessonEditor(lesson: LessonDto?, busy: Boolean, serverError: String?, onDismiss: () -> Unit, onSave: (LessonInput) -> Unit) {
    val s = LocalLabels.current
    var subject by rememberSaveable(lesson?.id) { mutableStateOf(lesson?.subject.orEmpty()) }
    var day by rememberSaveable(lesson?.id) { mutableStateOf((lesson?.dayOfWeek ?: 1).toString()) }
    var start by rememberSaveable(lesson?.id) { mutableStateOf(lesson?.startTime?.take(5) ?: "09:00") }
    var end by rememberSaveable(lesson?.id) { mutableStateOf(lesson?.endTime?.take(5) ?: "09:50") }
    var parity by rememberSaveable(lesson?.id) { mutableStateOf(lesson?.parity ?: "all") }
    var type by rememberSaveable(lesson?.id) { mutableStateOf(lesson?.lessonType.orEmpty()) }
    var room by rememberSaveable(lesson?.id) { mutableStateOf(lesson?.location.orEmpty()) }
    var teacher by rememberSaveable(lesson?.id) { mutableStateOf(lesson?.teacher.orEmpty()) }
    var error by rememberSaveable { mutableStateOf<String?>(null) }
    EditorDialog(s[if (lesson == null) Msg.ADD_LESSON else Msg.EDIT], busy, error ?: serverError, onDismiss, {
        val times = runCatching { LocalTime.parse(start) to LocalTime.parse(end) }.getOrNull()
        when {
            subject.isBlank() -> error = s[Msg.INVALID_FORM]
            times == null || times.second <= times.first -> error = s[Msg.INVALID_TIME]
            else -> { error = null; onSave(LessonInput(subject.trim(), day.toInt(), times.first.toString(), times.second.toString(), parity,
                type.trim().ifEmpty { null }, room.trim().ifEmpty { null }, teacher.trim().ifEmpty { null })) }
        }
    }) {
        Input(subject, { subject = it; error = null }, s[Msg.SUBJECT], 100, !busy)
        SectionTitle(s[Msg.DAY])
        ChoiceRow((1..7).map { it.toString() to s.weekday(it) }, day, { day = it }, !busy)
        TimeInput(start, { start = it }, s[Msg.START], !busy)
        TimeInput(end, { end = it }, s[Msg.END], !busy)
        ChoiceRow(listOf("all" to s[Msg.ALL_WEEKS], "numerator" to s[Msg.NUMERATOR], "denominator" to s[Msg.DENOMINATOR]), parity, { parity = it }, !busy)
        Input(type, { type = it }, s[Msg.TYPE] + " · " + s[Msg.OPTIONAL], 50, !busy)
        Input(room, { room = it }, s[Msg.ROOM] + " · " + s[Msg.OPTIONAL], 100, !busy)
        Input(teacher, { teacher = it }, s[Msg.TEACHER] + " · " + s[Msg.OPTIONAL], 100, !busy)
    }
}

@Composable
fun PasswordEditor(busy: Boolean, serverError: String?, onDismiss: () -> Unit, onSave: (String, String) -> Unit) {
    val s = LocalLabels.current
    // Passwords are deliberately not persisted in saved instance state.
    var old by remember { mutableStateOf("") }
    var new by remember { mutableStateOf("") }
    var repeated by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    EditorDialog(s[Msg.CHANGE_PASSWORD], busy, error ?: serverError, onDismiss, {
        when {
            new.length !in 10..128 || old.length !in 10..128 -> error = s[Msg.CREDENTIAL_HINT]
            new != repeated -> error = s[Msg.PASSWORD_MISMATCH]
            else -> { error = null; onSave(old, new) }
        }
    }) {
        PasswordInput(old, { old = it }, s[Msg.CURRENT_PASSWORD], !busy)
        PasswordInput(new, { new = it }, s[Msg.NEW_PASSWORD], !busy)
        PasswordInput(repeated, { repeated = it }, s[Msg.REPEAT_PASSWORD], !busy)
    }
}

@Composable
fun PasswordInput(value: String, onChange: (String) -> Unit, label: String, enabled: Boolean) {
    OutlinedTextField(value, { onChange(it.take(128)) }, Modifier.fillMaxWidth(), label = { Text(label) }, singleLine = true,
        visualTransformation = PasswordVisualTransformation(), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password), enabled = enabled)
}
