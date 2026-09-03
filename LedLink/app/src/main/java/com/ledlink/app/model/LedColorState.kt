package com.ledlink.app.model

/** Current color/power state shown in the UI and sent to whichever backend is connected. */
data class LedColorState(
    val red: Int = 255,
    val green: Int = 80,
    val blue: Int = 200,
    val brightness: Int = 100, // 0-100, cloud backends (Govee) take this separately from RGB
    val on: Boolean = true,
)
