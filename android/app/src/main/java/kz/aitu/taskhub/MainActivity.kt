package kz.aitu.taskhub

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import kz.aitu.taskhub.ui.TaskHubApp
import kz.aitu.taskhub.ui.theme.TaskHubTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            TaskHubTheme {
                TaskHubApp()
            }
        }
    }
}
