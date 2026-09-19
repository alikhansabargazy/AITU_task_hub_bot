package kz.aitu.taskhub.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import kz.aitu.taskhub.BuildConfig
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SessionStore(context: Context) {
    private val prefs = context.getSharedPreferences("taskhub_private", Context.MODE_PRIVATE)
    val baseUrl: String get() = prefs.getString("base_url", BuildConfig.API_BASE_URL)!!
    val language: String get() = prefs.getString("language", "ru")!!
    val expiresAt: String? get() = prefs.getString("expires_at", null)
    val revision: Long get() = prefs.getLong("revision", 0)

    fun markChanged() = synchronized(LOCK) { prefs.edit().putLong("revision", revision + 1).commit(); Unit }

    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }

    val token: String?
        get() = synchronized(LOCK) {
            val saved = prefs.getString("session", null) ?: return@synchronized null
            runCatching {
                val parts = saved.split(":")
                val cipher = Cipher.getInstance("AES/GCM/NoPadding")
                cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)))
                String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), Charsets.UTF_8)
            }.getOrNull()
        }

    fun saveSession(session: SessionDto) = synchronized(LOCK) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val encoded = Base64.encodeToString(cipher.iv, Base64.NO_WRAP) + ":" +
            Base64.encodeToString(cipher.doFinal(session.accessToken.toByteArray(Charsets.UTF_8)), Base64.NO_WRAP)
        check(prefs.edit().putString("session", encoded).putString("expires_at", session.expiresAt)
            .remove("snapshot").putLong("revision", revision + 1).commit())
    }

    fun setBaseUrl(url: String) = synchronized(LOCK) {
        require(token == null) { "Sign out before changing the server" }
        prefs.edit().putString("base_url", TaskHubNetwork.normalizeUrl(url)).remove("snapshot").apply()
    }

    fun setLanguage(language: String) { prefs.edit().putString("language", language).apply() }

    fun clearSession() = synchronized(LOCK) {
        prefs.edit().remove("session").remove("expires_at").remove("snapshot").putLong("revision", revision + 1).commit()
        Unit
    }

    fun invalidate(expectedToken: String): Boolean = synchronized(LOCK) {
        if (token != expectedToken) return@synchronized false
        clearSession()
        true
    }

    fun cachedSnapshot(): Snapshot? = synchronized(LOCK) {
        if (token == null) return@synchronized null
        runCatching { TaskHubNetwork.gson.fromJson(prefs.getString("snapshot", null), Snapshot::class.java) }.getOrNull()
    }

    fun saveSnapshot(snapshot: Snapshot, expectedToken: String, expectedUrl: String, expectedRevision: Long? = null): Boolean = synchronized(LOCK) {
        if (token != expectedToken || baseUrl != expectedUrl || (expectedRevision != null && revision != expectedRevision)) return@synchronized false
        prefs.edit().putString("snapshot", TaskHubNetwork.gson.toJson(snapshot))
            .putString("language", snapshot.profile.language).putLong("revision", revision + 1).commit()
    }

    companion object {
        private const val KEY_ALIAS = "taskhub-session-v1"
        private val LOCK = Any()
    }
}
