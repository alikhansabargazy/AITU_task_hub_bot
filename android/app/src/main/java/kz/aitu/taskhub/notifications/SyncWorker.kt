package kz.aitu.taskhub.notifications

import android.content.Context
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import kotlinx.coroutines.CancellationException
import kz.aitu.taskhub.data.SessionStore
import kz.aitu.taskhub.data.TaskHubNetwork
import kz.aitu.taskhub.data.TaskRepository
import retrofit2.HttpException
import java.util.concurrent.TimeUnit

class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val store = SessionStore(applicationContext)
        val token = store.token ?: return Result.success()
        val url = store.baseUrl
        val revision = store.revision
        return try {
            val snapshot = TaskRepository(TaskHubNetwork.api(url, token)).snapshot()
            if (store.saveSnapshot(snapshot, token, url, revision)) ReminderScheduler.reschedule(applicationContext)
            Result.success()
        } catch (error: CancellationException) {
            throw error
        } catch (error: Exception) {
            if (error is HttpException && error.code() == 401) {
                if (store.invalidate(token)) {
                    ReminderScheduler.cancelAll(applicationContext)
                }
                Result.failure()
            } else Result.retry()
        }
    }

    companion object {
        private const val NAME = "taskhub-sync"
        fun schedule(context: Context) {
            val work = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(NAME, ExistingPeriodicWorkPolicy.KEEP, work)
        }
        fun cancel(context: Context) { WorkManager.getInstance(context).cancelUniqueWork(NAME) }
    }
}
