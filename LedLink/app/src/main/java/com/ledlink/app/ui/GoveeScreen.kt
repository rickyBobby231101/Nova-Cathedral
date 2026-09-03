package com.ledlink.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
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
import com.ledlink.app.govee.GoveeDevice

@Composable
fun GoveeScreen(viewModel: AppViewModel) {
    var apiKey by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf<GoveeDevice?>(null) }
    val devices by viewModel.goveeDevices.collectAsState()
    val error by viewModel.goveeError.collectAsState()
    val color by viewModel.color.collectAsState()

    Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
        Text(
            "Govee devices are controlled through Govee's cloud API, not local BLE — " +
                "get a free key from the Govee Home app under Settings > About Us > Apply for API Key.",
        )
        OutlinedTextField(
            value = apiKey,
            onValueChange = { apiKey = it },
            label = { Text("Govee API key") },
            modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
        )
        Button(onClick = { viewModel.connectGovee(apiKey) }) { Text("Load devices") }

        error?.let { Text(it, modifier = Modifier.padding(top = 8.dp)) }

        if (selected != null) {
            Text("Controlling: ${selected!!.name}", modifier = Modifier.padding(top = 12.dp))
            ColorControls(state = color, onChange = viewModel::setColor, onPowerChange = viewModel::setPower)
        } else {
            LazyColumn(modifier = Modifier.padding(top = 12.dp)) {
                items(devices) { device: GoveeDevice ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                selected = device
                                viewModel.selectGoveeDevice(device)
                            }
                            .padding(vertical = 12.dp)
                    ) {
                        Text("${device.name} (${device.model})")
                    }
                    HorizontalDivider()
                }
            }
        }
    }
}
