package com.ledlink.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Magenta = Color(0xFFFF5EF1)
private val Cyan = Color(0xFF00E5FF)
private val DarkBackground = Color(0xFF12131A)

private val LedLinkDarkColors = darkColorScheme(
    primary = Magenta,
    secondary = Cyan,
    background = DarkBackground,
    surface = Color(0xFF1B1D27),
)

private val LedLinkLightColors = lightColorScheme(
    primary = Magenta,
    secondary = Cyan,
)

@Composable
fun LedLinkTheme(content: @Composable () -> Unit) {
    val colors = if (isSystemInDarkTheme()) LedLinkDarkColors else LedLinkLightColors
    MaterialTheme(colorScheme = colors, content = content)
}
