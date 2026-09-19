package kz.aitu.taskhub.ui

import android.Manifest
import android.app.NotificationManager
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.google.gson.JsonObject
import kz.aitu.taskhub.notifications.ReminderScheduler
import java.time.ZoneId

@Composable
fun LoginScreen(state: TaskUiState, vm: TaskViewModel) {
    val s = LocalLabels.current
    var registration by rememberSaveable { mutableStateOf(false) }
    var url by rememberSaveable { mutableStateOf(state.baseUrl) }
    var username by rememberSaveable { mutableStateOf("") }
    var name by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var repeat by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    Surface(Modifier.fillMaxSize()) {
        Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().imePadding().verticalScroll(rememberScrollState()).padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Spacer(Modifier.height(24.dp))
            Text("TaskHub", style = MaterialTheme.typography.displaySmall, fontWeight = FontWeight.Bold)
            Text(s[Msg.AUTH_HINT], color = MaterialTheme.colorScheme.onSurfaceVariant)
            ChoiceRow(listOf("ru" to "Русский", "en" to "English", "kk" to "Қазақша"), state.language, vm::setLoginLanguage, !state.isWorking)
            ChoiceRow(listOf("login" to s[Msg.LOGIN], "register" to s[Msg.REGISTER]), if (registration) "register" else "login", {
                registration = it == "register"; error = null; vm.clearError()
            }, !state.isWorking)
            Input(url, { url = it }, s[Msg.SERVER], 512, !state.isWorking)
            Text(s[Msg.SERVER_HINT], style = MaterialTheme.typography.bodySmall)
            Input(username, { username = it; error = null }, s[Msg.USERNAME], 32, !state.isWorking)
            if (registration) Input(name, { name = it }, s[Msg.NAME], 80, !state.isWorking)
            PasswordInput(password, { password = it; error = null }, s[Msg.PASSWORD], !state.isWorking)
            if (registration) PasswordInput(repeat, { repeat = it; error = null }, s[Msg.REPEAT_PASSWORD], !state.isWorking)
            Text(s[Msg.CREDENTIAL_HINT], style = MaterialTheme.typography.bodySmall)
            (error ?: state.error)?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            state.notice?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
            if (state.isWorking) LinearProgressIndicator(Modifier.fillMaxWidth())
            Button(onClick = {
                when {
                    !username.trim().lowercase().matches(Regex("[a-z0-9_]{3,32}")) || password.length !in 10..128 -> error = s[Msg.CREDENTIAL_HINT]
                    registration && password != repeat -> error = s[Msg.PASSWORD_MISMATCH]
                    else -> { error = null; vm.authenticate(url, username, password, name, registration) }
                }
            }, enabled = !state.isWorking, modifier = Modifier.fillMaxWidth()) { Text(s[if (registration) Msg.REGISTER else Msg.LOGIN]) }
        }
    }
}

@Composable
fun SettingsScreen(state: TaskUiState, vm: TaskViewModel) {
    val s = LocalLabels.current
    val profile = state.snapshot?.profile ?: return
    val context = LocalContext.current
    val busy = state.isWorking || state.isLoading
    var timezone by rememberSaveable(profile.timezone) { mutableStateOf(profile.timezone) }
    var zoneError by remember { mutableStateOf(false) }
    var passwordDialog by rememberSaveable { mutableStateOf(false) }
    var logoutDialog by rememberSaveable { mutableStateOf(false) }
    var notificationAllowed by remember { mutableStateOf(requireNotNull(context.getSystemService(NotificationManager::class.java)).areNotificationsEnabled()) }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        notificationAllowed = it
        ReminderScheduler.reschedule(context)
    }
    if (passwordDialog) PasswordEditor(busy, state.error, { passwordDialog = false }) { old, new -> vm.changePassword(old, new) { passwordDialog = false } }
    if (logoutDialog) AlertDialog(onDismissRequest = { if (!busy) logoutDialog = false }, title = { Text(s[Msg.LOGOUT_CONFIRM]) },
        confirmButton = { TextButton(onClick = { logoutDialog = false; vm.logout() }, enabled = !busy) { Text(s[Msg.LOGOUT]) } },
        dismissButton = { TextButton(onClick = { logoutDialog = false }, enabled = !busy) { Text(s[Msg.CANCEL]) } })

    fun setting(key: String, value: Int) { vm.updateSettings(JsonObject().apply { addProperty(key, value) }) }
    fun settingBool(key: String, value: Boolean) { vm.updateSettings(JsonObject().apply { addProperty(key, value) }) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(profile.displayName, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text("@" + profile.username)
        Text(state.baseUrl, style = MaterialTheme.typography.bodySmall)
        SectionTitle(s[Msg.LANGUAGE])
        ChoiceRow(listOf("ru" to "Русский", "en" to "English", "kk" to "Қазақша"), profile.language, {
            vm.updateSettings(JsonObject().apply { addProperty("language", it) })
        }, !busy)
        SectionTitle(s[Msg.TIMEZONE])
        Input(timezone, { timezone = it; zoneError = false }, "Asia/Almaty, Europe/Berlin, UTC…", 50, !busy)
        if (zoneError) Text(s[Msg.INVALID_FORM], color = MaterialTheme.colorScheme.error)
        OutlinedButton(enabled = !busy && timezone != profile.timezone, onClick = {
            if (runCatching { ZoneId.of(timezone.trim()) }.isFailure) zoneError = true
            else vm.updateSettings(JsonObject().apply { addProperty("timezone", timezone.trim()) })
        }) { Text(s[Msg.SAVE]) }
        Text(s[Msg.TIME_NOTE], style = MaterialTheme.typography.bodySmall)
        HorizontalDivider()
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(s[Msg.REMINDERS], Modifier.weight(1f))
            Switch(profile.notificationsEnabled, { settingBool("notifications_enabled", it) }, enabled = !busy)
        }
        SectionTitle(s[Msg.REMINDER_MINUTES])
        ChoiceRow(listOf(0, 5, 10, 15, 30, 60).map { it.toString() to if (it == 0) s[Msg.AT_START] else it.toString() },
            profile.reminderMinutes.toString(), { setting("reminder_minutes", it.toInt()) }, !busy)
        OutlinedButton(onClick = {
            if (Build.VERSION.SDK_INT >= 33 && !notificationAllowed) permission.launch(Manifest.permission.POST_NOTIFICATIONS)
            else context.startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName))
        }) { Text(s[if (notificationAllowed) Msg.NOTIFICATIONS_ON else Msg.ALLOW_NOTIFICATIONS]) }
        if (Build.VERSION.SDK_INT >= 31) OutlinedButton(onClick = {
            if (!ReminderScheduler.exactAllowed(context)) context.startActivity(Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:" + context.packageName)))
        }) { Text(s[if (ReminderScheduler.exactAllowed(context)) Msg.EXACT_ON else Msg.ALLOW_EXACT]) }
        Text(s[Msg.REMINDER_NOTE], style = MaterialTheme.typography.bodySmall)
        HorizontalDivider()
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(s[Msg.PARITY_OFFSET], Modifier.weight(1f))
            Switch(profile.weekParityOffset == 1, { setting("week_parity_offset", if (it) 1 else 0) }, enabled = !busy)
        }
        Text(s[Msg.PARITY_NOTE], style = MaterialTheme.typography.bodySmall)
        SectionTitle(s[Msg.HORIZON])
        ChoiceRow(listOf(1, 3, 7, 14).map { it.toString() to it.toString() }, profile.dashboardDays.toString(), { setting("dashboard_days", it.toInt()) }, !busy)
        HorizontalDivider()
        OutlinedButton(onClick = { vm.clearError(); passwordDialog = true }, enabled = !busy) { Text(s[Msg.CHANGE_PASSWORD]) }
        TextButton(onClick = { logoutDialog = true }, enabled = !busy) { Text(s[Msg.LOGOUT], color = MaterialTheme.colorScheme.error) }
        Spacer(Modifier.height(24.dp))
    }
}
