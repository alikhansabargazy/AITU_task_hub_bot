package kz.aitu.taskhub.data

import com.google.gson.GsonBuilder
import kz.aitu.taskhub.BuildConfig
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object TaskHubNetwork {
    // Explicit nulls clear optional fields in PATCH requests.
    val gson = GsonBuilder().serializeNulls().create()

    fun normalizeUrl(value: String): String {
        val url = value.trim().trimEnd('/').plus('/').toHttpUrl()
        require(url.username.isEmpty() && url.password.isEmpty() && url.query == null && url.fragment == null)
        require(BuildConfig.DEBUG || url.isHttps) { "HTTPS is required for release builds" }
        return url.toString()
    }

    fun api(baseUrl: String, token: String?): TaskHubApi {
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS).callTimeout(30, TimeUnit.SECONDS)
            .followRedirects(false).followSslRedirects(false)
            .addInterceptor { chain ->
                val request = chain.request().newBuilder()
                if (token != null) request.header("Authorization", "Bearer $token")
                chain.proceed(request.build())
            }.build()
        return Retrofit.Builder().baseUrl(normalizeUrl(baseUrl)).client(client)
            .addConverterFactory(GsonConverterFactory.create(gson)).build()
            .create(TaskHubApi::class.java)
    }
}
