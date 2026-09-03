package com.ledlink.app

import android.app.Application
import android.bluetooth.BluetoothDevice
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.ledlink.app.ble.BleLedController
import com.ledlink.app.ble.BleScanner
import com.ledlink.app.ble.LedConnectionState
import com.ledlink.app.ble.ScannedDevice
import com.ledlink.app.govee.GoveeCloudClient
import com.ledlink.app.govee.GoveeDevice
import com.ledlink.app.model.LedColorState
import com.ledlink.app.sync.ColorSyncManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class AppViewModel(application: Application) : AndroidViewModel(application) {

    private val bleScanner = BleScanner(application)
    val bleController = BleLedController(application)
    private val syncManager = ColorSyncManager(application)

    private var goveeClient: GoveeCloudClient? = null
    private var scanJob: Job? = null
    private var syncScanJob: Job? = null

    val color: StateFlow<LedColorState> get() = _color
    private val _color = MutableStateFlow(LedColorState())

    val connectionState: StateFlow<LedConnectionState> get() = bleController.state

    val scannedDevices: StateFlow<List<ScannedDevice>> get() = _scannedDevices
    private val _scannedDevices = MutableStateFlow<List<ScannedDevice>>(emptyList())

    val goveeDevices: StateFlow<List<GoveeDevice>> get() = _goveeDevices
    private val _goveeDevices = MutableStateFlow<List<GoveeDevice>>(emptyList())
    private var selectedGoveeDevice: GoveeDevice? = null

    val goveeError: StateFlow<String?> get() = _goveeError
    private val _goveeError = MutableStateFlow<String?>(null)

    val syncEnabled: StateFlow<Boolean> get() = _syncEnabled
    private val _syncEnabled = MutableStateFlow(false)
    private var syncSessionId: Int = 1

    fun startScan() {
        scanJob?.cancel()
        _scannedDevices.value = emptyList()
        scanJob = viewModelScope.launch(Dispatchers.IO) {
            bleScanner.scan().collect { found ->
                _scannedDevices.update { list ->
                    if (list.any { it.address == found.address }) {
                        list.map { if (it.address == found.address) found else it }
                    } else {
                        list + found
                    }
                }
            }
        }
    }

    fun stopScan() {
        scanJob?.cancel()
        scanJob = null
    }

    fun connect(device: BluetoothDevice) {
        stopScan()
        bleController.connect(device)
    }

    fun disconnect() = bleController.disconnect()

    fun setColor(newColor: LedColorState) {
        _color.value = newColor
        if (connectionState.value == LedConnectionState.READY) {
            bleController.sendColor(newColor)
        }
        selectedGoveeDevice?.let { device ->
            viewModelScope.launch(Dispatchers.IO) {
                runCatching { goveeClient?.setColor(device, newColor.red, newColor.green, newColor.blue) }
            }
        }
        if (_syncEnabled.value) {
            syncManager.startAdvertising(syncSessionId, newColor)
        }
    }

    fun setPower(on: Boolean) {
        setColor(_color.value.copy(on = on))
        if (connectionState.value == LedConnectionState.READY) {
            bleController.sendPower(on)
        }
        selectedGoveeDevice?.let { device ->
            viewModelScope.launch(Dispatchers.IO) {
                runCatching { goveeClient?.setPower(device, on) }
            }
        }
    }

    fun connectGovee(apiKey: String) {
        _goveeError.value = null
        val client = GoveeCloudClient(apiKey)
        goveeClient = client
        viewModelScope.launch(Dispatchers.IO) {
            runCatching { client.listDevices() }
                .onSuccess { _goveeDevices.value = it }
                .onFailure { _goveeError.value = it.message ?: "Failed to reach Govee" }
        }
    }

    fun selectGoveeDevice(device: GoveeDevice) {
        selectedGoveeDevice = device
    }

    fun setSyncEnabled(enabled: Boolean, sessionId: Int) {
        syncSessionId = sessionId
        _syncEnabled.value = enabled
        syncScanJob?.cancel()
        if (enabled) {
            syncManager.startAdvertising(sessionId, _color.value)
            syncScanJob = viewModelScope.launch(Dispatchers.IO) {
                syncManager.peerColors(sessionId).collect { peerColor ->
                    _color.value = peerColor
                    if (connectionState.value == LedConnectionState.READY) {
                        bleController.sendColor(peerColor)
                    }
                }
            }
        } else {
            syncManager.stopAdvertising()
        }
    }

    override fun onCleared() {
        super.onCleared()
        bleController.disconnect()
        syncManager.stopAdvertising()
    }
}
