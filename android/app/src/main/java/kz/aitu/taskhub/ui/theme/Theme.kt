package kz.aitu.taskhub.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColors = lightColorScheme(
    primary = TaskHubPrimary,
    background = TaskHubBackground,
    surface = androidx.compose.ui.graphics.Color.White,
)

private val DarkColors = darkColorScheme(
    primary = TaskHubPrimaryDark,
    background = TaskHubBackgroundDark,
    surface = androidx.compose.ui.graphics.Color(0xFF1B1B25),
)

@Composable
fun TaskHubTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        content = content,
    )
}
