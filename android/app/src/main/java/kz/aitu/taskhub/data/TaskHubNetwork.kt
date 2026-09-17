package kz.aitu.taskhub.data

import kz.aitu.taskhub.BuildConfig
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object TaskHubNetwork {
    val api: TaskHubApi by lazy {
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(TaskHubApi::class.java)
    }
}
