package kz.aitu.taskhub.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.repeatOnLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.delay
import kz.aitu.taskhub.data.*
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter

private enum class Tab(val title: Msg) { HOME(Msg.HOME), TASKS(Msg.TASKS), SCHEDULE(Msg.SCHEDULE), SETTINGS(Msg.SETTINGS) }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaskHubApp(viewModel: TaskViewModel = viewModel()) {
    val state = viewModel.uiState.collectAsStateWithLifecycle().value
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    LaunchedEffect(viewModel, lifecycle) {
        lifecycle.repeatOnLifecycle(Lifecycle.State.RESUMED) {
            while (true) {
                viewModel.refresh()
                delay(60_000)
            }
        }
    }
    CompositionLocalProvider(LocalLabels provides Labels(state.language)) {
        if (!state.authenticated) {
            LoginScreen(state, viewModel)
            return@CompositionLocalProvider
        }
        val s = LocalLabels.current
        val snapshot = state.snapshot
        val busy = state.isWorking || state.isLoading
        var tabName by rememberSaveable { mutableStateOf(Tab.HOME.name) }
        val tab = Tab.valueOf(tabName)
        var taskEditor by rememberSaveable { mutableStateOf(false) }
        var taskId by rememberSaveable { mutableStateOf<Long?>(null) }
        var lessonEditor by rememberSaveable { mutableStateOf(false) }
        var lessonId by rememberSaveable { mutableStateOf<Long?>(null) }
        var deleteTaskId by rememberSaveable { mutableStateOf<Long?>(null) }
        var deleteLessonId by rememberSaveable { mutableStateOf<Long?>(null) }

        fun editTask(task: TaskDto?) {
            viewModel.clearError()
            taskId = task?.id
            taskEditor = true
        }
        fun editLesson(lesson: LessonDto?) {
            viewModel.clearError()
            lessonId = lesson?.id
            lessonEditor = true
        }

        if (taskEditor) {
            val original = snapshot?.tasks?.find { it.id == taskId }
            TaskEditor(original, busy, state.error, { taskEditor = false }) {
                viewModel.saveTask(original, it) { taskEditor = false }
            }
        }
        if (lessonEditor) {
            val original = snapshot?.lessons?.find { it.id == lessonId }
            LessonEditor(original, busy, state.error, { lessonEditor = false }) {
                viewModel.saveLesson(original, it) { lessonEditor = false }
            }
        }
        snapshot?.tasks?.find { it.id == deleteTaskId }?.let { task ->
            DeleteDialog(task.text, busy, { deleteTaskId = null }) { viewModel.deleteTask(task) { deleteTaskId = null } }
        }
        snapshot?.lessons?.find { it.id == deleteLessonId }?.let { lesson ->
            DeleteDialog(lesson.subject, busy, { deleteLessonId = null }) { viewModel.deleteLesson(lesson) { deleteLessonId = null } }
        }

        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Column { Text("TaskHub", fontWeight = FontWeight.Bold); Text(s[tab.title], style = MaterialTheme.typography.labelLarge) } },
                    actions = { IconButton(onClick = viewModel::refresh, enabled = !busy) { Icon(Icons.Default.Refresh, s[Msg.REFRESH]) } },
                )
            },
            bottomBar = {
                NavigationBar {
                    Tab.entries.forEach { item ->
                        NavigationBarItem(selected = tab == item, onClick = { tabName = item.name },
                            icon = { Icon(when (item) { Tab.HOME -> Icons.Default.Home; Tab.TASKS -> Icons.Default.CheckCircle; Tab.SCHEDULE -> Icons.Default.DateRange; Tab.SETTINGS -> Icons.Default.Settings }, s[item.title]) },
                            label = { Text(s[item.title], maxLines = 1) })
                    }
                }
            },
            floatingActionButton = {
                if (snapshot != null && tab != Tab.SETTINGS) {
                    FloatingActionButton(onClick = {
                        if (!busy) { if (tab == Tab.SCHEDULE) editLesson(null) else editTask(null) }
                    }) { Icon(Icons.Default.Add, s[if (tab == Tab.SCHEDULE) Msg.ADD_LESSON else Msg.ADD_TASK]) }
                }
            },
        ) { padding ->
            Column(Modifier.fillMaxSize().padding(padding)) {
                if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                state.error?.let { ErrorBanner(it, viewModel::clearError) }
                state.notice?.let { Text(it, Modifier.padding(12.dp), color = MaterialTheme.colorScheme.primary) }
                if (state.offline) Text(s[Msg.CACHE_NOTICE], Modifier.padding(12.dp), style = MaterialTheme.typography.bodySmall)
                if (snapshot == null) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Button(onClick = viewModel::refresh, enabled = !busy) { Text(s[Msg.RETRY]) }
                    }
                } else when (tab) {
                    Tab.HOME -> DashboardScreen(snapshot) { tabName = Tab.TASKS.name; viewModel.setFilter(TaskFilter.ACTIVE) }
                    Tab.TASKS -> TasksScreen(state, viewModel, !busy, ::editTask) { deleteTaskId = it.id; viewModel.clearError() }
                    Tab.SCHEDULE -> ScheduleScreen(snapshot, !busy, ::editLesson) { deleteLessonId = it.id; viewModel.clearError() }
                    Tab.SETTINGS -> SettingsScreen(state, viewModel)
                }
            }
        }
    }
}

@Composable
fun ErrorBanner(message: String, onDismiss: () -> Unit = {}) {
    val s = LocalLabels.current
    Surface(color = MaterialTheme.colorScheme.errorContainer, modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(message, Modifier.weight(1f), style = MaterialTheme.typography.bodySmall)
            IconButton(onClick = onDismiss) { Icon(Icons.Default.Close, s[Msg.CLOSE]) }
        }
    }
}

@Composable
private fun DeleteDialog(name: String, busy: Boolean, onDismiss: () -> Unit, onDelete: () -> Unit) {
    val s = LocalLabels.current
    AlertDialog(onDismissRequest = { if (!busy) onDismiss() }, title = { Text(s[Msg.CONFIRM_DELETE, name]) },
        confirmButton = { TextButton(onClick = onDelete, enabled = !busy) { Text(s[Msg.DELETE], color = MaterialTheme.colorScheme.error) } },
        dismissButton = { TextButton(onClick = onDismiss, enabled = !busy) { Text(s[Msg.CANCEL]) } })
}

@Composable
private fun TasksScreen(state: TaskUiState, vm: TaskViewModel, enabled: Boolean, onEdit: (TaskDto) -> Unit, onDelete: (TaskDto) -> Unit) {
    val s = LocalLabels.current
    OutlinedTextField(state.search, vm::setSearch, Modifier.fillMaxWidth().padding(horizontal = 16.dp), label = { Text(s[Msg.SEARCH]) }, singleLine = true)
    ChoiceRow(TaskFilter.entries.map { it.name to s[when (it) { TaskFilter.ALL -> Msg.ALL; TaskFilter.ACTIVE -> Msg.ACTIVE; TaskFilter.COMPLETED -> Msg.DONE }] },
        state.filter.name, { vm.setFilter(TaskFilter.valueOf(it)) })
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp, 8.dp, 16.dp, 100.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (state.visibleTasks.isEmpty()) item { Text(s[Msg.EMPTY]) }
        items(state.visibleTasks, key = TaskDto::id) { task ->
            TaskCard(task, enabled, { vm.setCompleted(task, it) }, { onEdit(task) }, { onDelete(task) })
        }
    }
}

@Composable
private fun TaskCard(task: TaskDto, enabled: Boolean, onCompleted: (Boolean) -> Unit, onEdit: () -> Unit, onDelete: () -> Unit) {
    val s = LocalLabels.current
    Card(shape = RoundedCornerShape(20.dp), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(task.isCompleted, onCompleted, enabled = enabled)
                Column(Modifier.weight(1f)) {
                    Text(task.text, fontWeight = FontWeight.SemiBold, textDecoration = if (task.isCompleted) TextDecoration.LineThrough else null)
                    task.subjectName?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary) }
                }
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f).padding(start = 12.dp)) {
                    Text(task.deadline?.let(::formatDeadline) ?: s[Msg.NO_DEADLINE], style = MaterialTheme.typography.labelMedium)
                    if (task.priority == "high") Text(s[Msg.HIGH], color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.labelMedium)
                }
                IconButton(onClick = onEdit, enabled = enabled) { Icon(Icons.Default.Edit, s[Msg.EDIT]) }
                IconButton(onClick = onDelete, enabled = enabled) { Icon(Icons.Default.DeleteOutline, s[Msg.DELETE]) }
            }
        }
    }
}

@Composable
private fun ScheduleScreen(snapshot: Snapshot, enabled: Boolean, onEdit: (LessonDto) -> Unit, onDelete: (LessonDto) -> Unit) {
    val s = LocalLabels.current
    var day by rememberSaveable { mutableStateOf("0") }
    var parity by rememberSaveable { mutableStateOf("any") }
    Text(s[Msg.ISO_WEEK, snapshot.dashboard.isoWeek] + " · " + s.parity(snapshot.dashboard.parity), Modifier.padding(horizontal = 16.dp))
    ChoiceRow(listOf("0" to s[Msg.WEEK]) + (1..7).map { it.toString() to s.weekday(it) }, day, { day = it })
    ChoiceRow(listOf("any" to s[Msg.ALL], "numerator" to s[Msg.NUMERATOR], "denominator" to s[Msg.DENOMINATOR]), parity, { parity = it })
    val lessons = snapshot.lessons.filter { (day == "0" || it.dayOfWeek == day.toInt()) && (parity == "any" || it.parity == "all" || it.parity == parity) }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp, 8.dp, 16.dp, 100.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (lessons.isEmpty()) item { Text(s[Msg.EMPTY]) }
        items(lessons, key = LessonDto::id) { lesson ->
            Card(Modifier.fillMaxWidth(), shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(s.weekday(lesson.dayOfWeek) + " · " + lesson.startTime.take(5) + "–" + lesson.endTime.take(5), color = MaterialTheme.colorScheme.primary)
                    Text(lesson.subject, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    listOfNotNull(lesson.lessonType, lesson.location, lesson.teacher).forEach { Text(it, style = MaterialTheme.typography.bodyMedium) }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(s.parity(lesson.parity), Modifier.weight(1f), style = MaterialTheme.typography.labelMedium)
                        IconButton(onClick = { onEdit(lesson) }, enabled = enabled) { Icon(Icons.Default.Edit, s[Msg.EDIT]) }
                        IconButton(onClick = { onDelete(lesson) }, enabled = enabled) { Icon(Icons.Default.DeleteOutline, s[Msg.DELETE]) }
                    }
                }
            }
        }
    }
}

@Composable
private fun DashboardScreen(snapshot: Snapshot, onTasks: () -> Unit) {
    val s = LocalLabels.current
    val data = snapshot.dashboard
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(16.dp, 16.dp, 16.dp, 100.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Text(s[Msg.HELLO, snapshot.profile.displayName], style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(formatDeadline(data.localNow) + " · " + data.timezone, style = MaterialTheme.typography.bodySmall)
        }
        item {
            Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(s[Msg.TODAY_COUNT, data.todayCount], style = MaterialTheme.typography.titleLarge)
                    Text(s[Msg.ACTIVE_COUNT, data.activeCount])
                    Text(s[Msg.ISO_WEEK, data.isoWeek] + " · " + s.parity(data.parity))
                }
            }
        }
        item { SectionTitle(s[Msg.CURRENT]); if (data.currentLessons.isEmpty()) Text(s[Msg.NO_CLASS]) }
        items(data.currentLessons, key = { "current-${it.lesson.id}" }) { OccurrenceCard(it) }
        item { SectionTitle(s[Msg.NEXT]); data.nextLesson?.let { OccurrenceCard(it) } ?: Text(s[Msg.NO_NEXT]) }
        listOf(Msg.OVERDUE to data.overdue, Msg.UPCOMING to data.upcoming, Msg.NO_DEADLINE to data.undated).forEach { (title, tasks) ->
            item {
                SectionTitle(s[title] + " · " + tasks.size)
                if (tasks.isEmpty()) Text(s[Msg.EMPTY], style = MaterialTheme.typography.bodySmall)
            }
            items(tasks.take(5), key = { "${title.name}-${it.id}" }) { task ->
                OutlinedCard(onClick = onTasks, modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(14.dp)) {
                        Text(task.text, fontWeight = FontWeight.Medium)
                        task.deadline?.let { Text(formatDeadline(it), style = MaterialTheme.typography.bodySmall) }
                    }
                }
            }
            if (tasks.size > 5) item { TextButton(onClick = onTasks) { Text(s[Msg.MORE, tasks.size]) } }
        }
        item { Text(s[Msg.HORIZON] + ": " + data.dashboardDays + " · " + s[Msg.LATER, data.laterCount], style = MaterialTheme.typography.bodySmall) }
    }
}

@Composable
private fun OccurrenceCard(occurrence: LessonOccurrence) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(occurrence.lesson.subject, fontWeight = FontWeight.SemiBold)
            Text(formatDeadline(occurrence.start) + "–" + occurrence.lesson.endTime.take(5))
            occurrence.lesson.location?.let { Text(it) }
            occurrence.lesson.teacher?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
        }
    }
}

@Composable
fun SectionTitle(title: String) { Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold, modifier = Modifier.padding(vertical = 8.dp)) }

@Composable
fun ChoiceRow(choices: List<Pair<String, String>>, selected: String, onSelected: (String) -> Unit, enabled: Boolean = true) {
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        choices.forEach { (value, label) -> FilterChip(selected == value, { onSelected(value) }, label = { Text(label) }, enabled = enabled) }
    }
}

fun formatDeadline(value: String): String = runCatching {
    val local = runCatching { OffsetDateTime.parse(value).toLocalDateTime() }.getOrElse { LocalDateTime.parse(value) }
    local.format(DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm"))
}.getOrDefault(value)
