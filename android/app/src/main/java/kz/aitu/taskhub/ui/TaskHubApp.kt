package kz.aitu.taskhub.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.DeleteOutline
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import kz.aitu.taskhub.data.TaskDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TaskHubApp(
    viewModel: TaskViewModel = viewModel(factory = TaskViewModel.Factory),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var showCreateDialog by remember { mutableStateOf(false) }

    if (showCreateDialog) {
        CreateTaskDialog(
            onDismiss = { showCreateDialog = false },
            onCreate = { text ->
                showCreateDialog = false
                viewModel.createTask(text)
            },
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("TaskHub", fontWeight = FontWeight.Bold)
                        Text(
                            text = "AITU · задачи и дедлайны",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                },
                actions = {
                    IconButton(
                        onClick = viewModel::refresh,
                        enabled = !state.isLoading && !state.isWorking,
                    ) {
                        Icon(Icons.Default.Refresh, contentDescription = "Обновить")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                ),
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { showCreateDialog = true },
                icon = { Icon(Icons.Default.Add, contentDescription = null) },
                text = { Text("Новая задача") },
                expanded = !state.isWorking,
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { contentPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(contentPadding),
        ) {
            FilterRow(
                selected = state.filter,
                onSelected = viewModel::setFilter,
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)

            when {
                state.isLoading -> LoadingState()
                state.error != null -> ErrorState(
                    message = state.error,
                    onRetry = viewModel::refresh,
                    onDismiss = viewModel::clearError,
                )
                state.visibleTasks.isEmpty() -> EmptyState(state.filter)
                else -> TaskList(
                    tasks = state.visibleTasks,
                    enabled = !state.isWorking,
                    onCompletedChange = viewModel::setCompleted,
                    onDelete = viewModel::deleteTask,
                )
            }
        }
    }
}

@Composable
private fun FilterRow(
    selected: TaskFilter,
    onSelected: (TaskFilter) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        listOf(
            TaskFilter.ACTIVE to "Активные",
            TaskFilter.COMPLETED to "Готовые",
            TaskFilter.ALL to "Все",
        ).forEach { (filter, title) ->
            FilterChip(
                selected = selected == filter,
                onClick = { onSelected(filter) },
                label = { Text(title) },
            )
        }
    }
}

@Composable
private fun TaskList(
    tasks: List<TaskDto>,
    enabled: Boolean,
    onCompletedChange: (TaskDto, Boolean) -> Unit,
    onDelete: (TaskDto) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(start = 16.dp, top = 16.dp, end = 16.dp, bottom = 104.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        items(tasks, key = TaskDto::id) { task ->
            TaskCard(
                task = task,
                enabled = enabled,
                onCompletedChange = { onCompletedChange(task, it) },
                onDelete = { onDelete(task) },
            )
        }
    }
}

@Composable
private fun TaskCard(
    task: TaskDto,
    enabled: Boolean,
    onCompletedChange: (Boolean) -> Unit,
    onDelete: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(14.dp),
            verticalAlignment = Alignment.Top,
        ) {
            Checkbox(
                checked = task.isCompleted,
                onCheckedChange = onCompletedChange,
                enabled = enabled,
            )
            Spacer(Modifier.width(8.dp))
            Column(
                modifier = Modifier
                    .weight(1f)
                    .padding(top = 10.dp),
            ) {
                Text(
                    text = task.text,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    textDecoration = if (task.isCompleted) TextDecoration.LineThrough else null,
                    color = if (task.isCompleted) {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    } else {
                        MaterialTheme.colorScheme.onSurface
                    },
                )
                if (!task.subjectName.isNullOrBlank()) {
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = task.subjectName,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
                Spacer(Modifier.height(8.dp))
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    if (task.priority == "high") {
                        StatusPill("Высокий", MaterialTheme.colorScheme.errorContainer)
                    }
                    task.deadline?.let {
                        Text(
                            text = formatDeadline(it),
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
            IconButton(onClick = onDelete, enabled = enabled) {
                Icon(
                    imageVector = Icons.Default.DeleteOutline,
                    contentDescription = "Удалить",
                    tint = MaterialTheme.colorScheme.error,
                )
            }
        }
    }
}

@Composable
private fun StatusPill(text: String, background: Color) {
    Surface(
        color = background,
        shape = RoundedCornerShape(50),
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            style = MaterialTheme.typography.labelSmall,
        )
    }
}

@Composable
private fun LoadingState() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        CircularProgressIndicator()
    }
}

@Composable
private fun EmptyState(filter: TaskFilter) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        contentAlignment = Alignment.Center,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("✓", style = MaterialTheme.typography.displayLarge, color = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.height(12.dp))
            Text(
                text = if (filter == TaskFilter.COMPLETED) {
                    "Выполненных задач пока нет"
                } else {
                    "Здесь пока нет задач"
                },
                style = MaterialTheme.typography.titleMedium,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = "Нажмите «Новая задача», чтобы добавить первую.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun ErrorState(
    message: String,
    onRetry: () -> Unit,
    onDismiss: () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        contentAlignment = Alignment.Center,
    ) {
        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
            Column(Modifier.padding(20.dp)) {
                Text("Не удалось загрузить задачи", fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(8.dp))
                Text(message, style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(16.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = onRetry) { Text("Повторить") }
                    OutlinedButton(onClick = onDismiss) { Text("Закрыть") }
                }
            }
        }
    }
}

@Composable
private fun CreateTaskDialog(
    onDismiss: () -> Unit,
    onCreate: (String) -> Unit,
) {
    var text by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Новая задача") },
        text = {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it.take(255) },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Что нужно сделать?") },
                minLines = 2,
                supportingText = { Text("${text.length}/255") },
            )
        },
        confirmButton = {
            Button(
                onClick = { onCreate(text.trim()) },
                enabled = text.isNotBlank(),
            ) {
                Text("Добавить")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Отмена") }
        },
    )
}

private fun formatDeadline(value: String): String = runCatching {
    LocalDateTime.parse(value).format(DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm"))
}.getOrDefault(value)
