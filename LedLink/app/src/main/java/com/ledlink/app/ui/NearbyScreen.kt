package com.ledlink.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ledlink.app.AppViewModel
import com.ledlink.app.ble.LedConnectionState
import com.ledlink.app.ble.ScannedDevice

@Composable
fun NearbyScreen(viewModel: AppViewModel, scanning: Boolean, onToggleScan: () -> Unit) {
    val devices by viewModel.scannedDevices.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()
    val color by viewModel.color.collectAsState()

    Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
            Text("Nearby BLE LED devices", style = androidx.compose.material3.MaterialTheme.typography.titleMedium)
            Button(onClick = onToggleScan) { Text(if (scanning) "Stop scan" else "Scan") }
        }

        Text("Status: ${connectionState.name}", modifier = Modifier.padding(vertical = 8.dp))

        if (connectionState == LedConnectionState.READY) {
            ColorControls(state = color, onChange = viewModel::setColor, onPowerChange = viewModel::setPower)
            Button(onClick = { viewModel.disconnect() }, modifier = Modifier.padding(top = 8.dp)) {
                Text("Disconnect")
            }
        } else {
            LazyColumn {
                items(devices) { scanned: ScannedDevice ->
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { viewModel.connect(scanned.device) }
                            .padding(vertical = 12.dp)
                    ) {
                        Text(scanned.name)
                        Text("${scanned.address}  •  RSSI ${scanned.rssi}")
                    }
                    HorizontalDivider()
                }
            }
        }
    }
}
