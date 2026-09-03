package com.ledlink.app.govee

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

data class GoveeDevice(
    val device: String,
    val model: String,
    val name: String,
)

/**
 * Minimal client for Govee's official "Developer API" (https://developer.govee.com).
 *
 * Many newer Govee bulbs/strips encrypt their local BLE traffic per-device, so there is no
 * generic BLE protocol that works across the Govee lineup the way Magic Home works for
 * generic clones. The supported path is Govee's cloud REST API instead: get a free API key
 * from the Govee Home app (Profile -> Settings -> About Us -> Apply for API Key), paste it
 * into the app's Govee tab, and control happens over the internet rather than locally.
 * This means Govee control here requires an internet connection; it will not work as a
 * purely local/offline BLE link the way the "Nearby" tab does.
 */
class GoveeCloudClient(private val apiKey: String) {

    private val client = OkHttpClient()
    private val jsonMedia = "application/json".toMediaType()
    private val baseUrl = "https://developer-api.govee.com/v1"

    @Throws(IOException::class)
    fun listDevices(): List<GoveeDevice> {
        val request = Request.Builder()
            .url("$baseUrl/devices")
            .addHeader("Govee-API-Key", apiKey)
            .get()
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Govee list devices failed: HTTP ${response.code}")
            val body = JSONObject(response.body?.string().orEmpty())
            val list = mutableListOf<GoveeDevice>()
            val dataArray = body.getJSONObject("data").getJSONArray("devices")
            for (i in 0 until dataArray.length()) {
                val entry = dataArray.getJSONObject(i)
                list.add(
                    GoveeDevice(
                        device = entry.getString("device"),
                        model = entry.getString("model"),
                        name = entry.optString("deviceName", entry.getString("model")),
                    )
                )
            }
            return list
        }
    }

    @Throws(IOException::class)
    fun setPower(target: GoveeDevice, on: Boolean) {
        sendControl(target, "turn", if (on) "on" else "off")
    }

    @Throws(IOException::class)
    fun setColor(target: GoveeDevice, red: Int, green: Int, blue: Int) {
        val value = JSONObject().put("r", red).put("g", green).put("b", blue)
        sendControl(target, "color", value)
    }

    @Throws(IOException::class)
    fun setBrightness(target: GoveeDevice, percent: Int) {
        sendControl(target, "brightness", percent.coerceIn(0, 100))
    }

    private fun sendControl(target: GoveeDevice, name: String, value: Any) {
        val payload = JSONObject().apply {
            put("device", target.device)
            put("model", target.model)
            put("cmd", JSONObject().put("name", name).put("value", value))
        }

        val request = Request.Builder()
            .url("$baseUrl/devices/control")
            .addHeader("Govee-API-Key", apiKey)
            .put(payload.toString().toRequestBody(jsonMedia))
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Govee control failed: HTTP ${response.code}")
        }
    }
}
