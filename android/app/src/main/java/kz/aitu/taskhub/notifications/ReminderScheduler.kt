package kz.aitu.taskhub.notifications

import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import kz.aitu.taskhub.MainActivity
import kz.aitu.taskhub.data.SessionStore
import kz.aitu.taskhub.data.TaskHubNetwork
import java.time.Instant

object ReminderScheduler {
    private const val CHANNEL = "classes"
    private const val ACTION = "kz.aitu.taskhub.REMINDER"
    private val lock = Any()
    private fun prefs(context: Context) = context.getSharedPreferences("reminder_plan", Context.MODE_PRIVATE)
    private fun plan(context: Context): List<ReminderEvent> = runCatching {
        TaskHubNetwork.gson.fromJson(prefs(context).getString("events", "[]"), Array<ReminderEvent>::class.java).toList()
    }.getOrDefault(emptyList())

    private fun intent(context: Context, event: ReminderEvent): PendingIntent = PendingIntent.getBroadcast(
        context, 0, Intent(context, ReminderReceiver::class.java).setAction(ACTION)
            .setData(Uri.parse("taskhub-reminder:" + Uri.encode(event.key))),
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
    )

    fun exactAllowed(context: Context): Boolean = Build.VERSION.SDK_INT < 31 || requireNotNull(context.getSystemService(AlarmManager::class.java)).canScheduleExactAlarms()

    fun cancelAll(context: Context) = synchronized(lock) {
        val alarms = requireNotNull(context.getSystemService(AlarmManager::class.java))
        plan(context).forEach { alarms.cancel(intent(context, it)) }
        prefs(context).edit().remove("events").commit()
        requireNotNull(context.getSystemService(NotificationManager::class.java)).cancelAll()
    }

    fun reschedule(context: Context) = synchronized(lock) {
        val store = SessionStore(context)
        val snapshot = store.cachedSnapshot()
        val valid = runCatching { Instant.parse(store.expiresAt).isAfter(Instant.now()) }.getOrDefault(false)
        val events = if (valid && snapshot != null) ReminderPlanner.events(snapshot.profile, snapshot.lessons, Instant.now()) else emptyList()
        val alarms = requireNotNull(context.getSystemService(AlarmManager::class.java))
        plan(context).forEach { alarms.cancel(intent(context, it)) }
        prefs(context).edit().putString("events", TaskHubNetwork.gson.toJson(events)).commit()
        events.forEach { event ->
            try {
                if (exactAllowed(context)) alarms.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, event.at, intent(context, event))
                else alarms.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, event.at, intent(context, event))
            } catch (_: SecurityException) {
                // Permission can be revoked between checking and scheduling.
                alarms.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, event.at, intent(context, event))
            }
        }
    }

    fun receive(context: Context, broadcast: Intent) = synchronized(lock) {
        if (broadcast.action != ACTION) {
            reschedule(context)
            if (SessionStore(context).token != null) SyncWorker.schedule(context)
            return@synchronized
        }
        val key = Uri.decode(broadcast.data?.schemeSpecificPart ?: return@synchronized)
        val events = plan(context)
        val event = events.firstOrNull { it.key == key } ?: return@synchronized
        prefs(context).edit().putString("events", TaskHubNetwork.gson.toJson(events.filterNot { it.key == key })).commit()
        val store = SessionStore(context)
        val valid = runCatching { Instant.parse(store.expiresAt).isAfter(Instant.now()) }.getOrDefault(false)
        val manager = requireNotNull(context.getSystemService(NotificationManager::class.java))
        if (store.token != null && valid && event.until > System.currentTimeMillis() && manager.areNotificationsEnabled()) {
            manager.createNotificationChannel(NotificationChannel(CHANNEL, "TaskHub", NotificationManager.IMPORTANCE_HIGH))
            val open = PendingIntent.getActivity(context, 0, Intent(context, MainActivity::class.java), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
            val notification = Notification.Builder(context, CHANNEL).setSmallIcon(android.R.drawable.ic_popup_reminder)
                .setContentTitle(event.title).setContentText(event.text).setStyle(Notification.BigTextStyle().bigText(event.text))
                .setContentIntent(open).setAutoCancel(true).build()
            try { manager.notify(event.key, 1, notification) } catch (_: SecurityException) { /* permission revoked */ }
        }
        reschedule(context)
    }
}

class ReminderReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) { ReminderScheduler.receive(context, intent) }
}
