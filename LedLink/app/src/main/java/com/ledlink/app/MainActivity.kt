package com.ledlink.app

import android.Manifest
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bluetooth
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.ledlink.app.ui.GoveeScreen
import com.ledlink.app.ui.NearbyScreen
import com.ledlink.app.ui.SyncScreen
import com.ledlink.app.ui.theme.LedLinkTheme

class MainActivity : ComponentActivity() {

    private val viewModel: AppViewModel by viewModels()

    private val requestPermissions = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { /* Scanning/advertising simply won't return results until granted; no extra handling needed. */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestPermissions.launch(requiredPermissions())

        setContent {
            LedLinkTheme {
                Surface(color = MaterialTheme.colorScheme.background) {
                    LedLinkApp(viewModel)
                }
            }
        }
    }

    private fun requiredPermissions(): Array<String> =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            arrayOf(
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_CONNECT,
                Manifest.permission.BLUETOOTH_ADVERTISE,
            )
        } else {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        }
}

private enum class Tab(val label: String) { NEARBY("Nearby"), GOVEE("Govee"), SYNC("Sync") }

@Composable
private fun LedLinkApp(viewModel: AppViewModel) {
    var tab by remember { mutableStateOf(Tab.NEARBY) }
    var scanning by remember { mutableStateOf(false) }

    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = tab == Tab.NEARBY,
                    onClick = { tab = Tab.NEARBY },
                    icon = { Icon(Icons.Filled.Bluetooth, contentDescription = null) },
                    label = { Text(Tab.NEARBY.label) },
                )
                NavigationBarItem(
                    selected = tab == Tab.GOVEE,
                    onClick = { tab = Tab.GOVEE },
                    icon = { Icon(Icons.Filled.Cloud, contentDescription = null) },
                    label = { Text(Tab.GOVEE.label) },
                )
                NavigationBarItem(
                    selected = tab == Tab.SYNC,
                    onClick = { tab = Tab.SYNC },
                    icon = { Icon(Icons.Filled.Sync, contentDescription = null) },
                    label = { Text(Tab.SYNC.label) },
                )
            }
        }
    ) { padding ->
        Surface(modifier = Modifier.padding(padding)) {
            when (tab) {
                Tab.NEARBY -> NearbyScreen(
                    viewModel = viewModel,
                    scanning = scanning,
                    onToggleScan = {
                        scanning = !scanning
                        if (scanning) viewModel.startScan() else viewModel.stopScan()
                    },
                )
                Tab.GOVEE -> GoveeScreen(viewModel)
                Tab.SYNC -> SyncScreen(viewModel)
            }
        }
    }
}
