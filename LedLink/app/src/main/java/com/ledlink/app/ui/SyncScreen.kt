package com.ledlink.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ledlink.app.AppViewModel

@Composable
fun SyncScreen(viewModel: AppViewModel) {
    var sessionText by remember { mutableStateOf("1") }
    val syncEnabled by viewModel.syncEnabled.collectAsState()
    val color by viewModel.color.collectAsState()

    Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
        Text(
            "Sync mode links phones running LedLink over Bluetooth (no internet, no pairing). " +
                "Everyone using the same session number nearby will mirror whichever phone " +
                "changes the color last. This only syncs other phones running this app — it " +
                "cannot link to closed festival-toy hardware that has no receiver.",
        )
        OutlinedTextField(
            value = sessionText,
            onValueChange = { sessionText = it.filter(Char::isDigit).take(3) },
            label = { Text("Session number (share with the group)") },
            modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
            enabled = !syncEnabled,
        )
        Button(onClick = {
            val session = sessionText.toIntOrNull()?.coerceIn(0, 255) ?: 1
            viewModel.setSyncEnabled(!syncEnabled, session)
        }) {
            Text(if (syncEnabled) "Stop syncing" else "Start syncing")
        }

        if (syncEnabled) {
            Text("Synced color:", modifier = Modifier.padding(top = 16.dp))
            ColorControls(state = color, onChange = viewModel::setColor, onPowerChange = viewModel::setPower)
        }
    }
}
