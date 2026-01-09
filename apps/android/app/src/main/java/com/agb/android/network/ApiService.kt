package com.agb.android.network

import retrofit2.http.GET

interface ApiService {
    @GET("health")
    suspend fun health(): Map<String, Any>
}
