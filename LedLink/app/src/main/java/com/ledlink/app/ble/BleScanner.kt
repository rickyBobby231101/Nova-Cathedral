package com.ledlink.app.ble

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

data class ScannedDevice(
    val device: BluetoothDevice,
    val name: String,
    val address: String,
    val rssi: Int,
)

/** Thin wrapper around [android.bluetooth.le.BluetoothLeScanner] exposed as a cold [Flow]. */
class BleScanner(context: Context) {

    private val adapter: BluetoothAdapter? =
        (context.getSystemService(Context.BLUETOOTH_SERVICE) as? android.bluetooth.BluetoothManager)?.adapter

    @SuppressLint("MissingPermission")
    fun scan(): Flow<ScannedDevice> = callbackFlow {
        val scanner = adapter?.bluetoothLeScanner
        if (scanner == null) {
            close(IllegalStateException("Bluetooth is not available or disabled"))
            return@callbackFlow
        }

        val callback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                val name = result.device.name ?: result.scanRecord?.deviceName ?: "Unknown device"
                trySend(
                    ScannedDevice(
                        device = result.device,
                        name = name,
                        address = result.device.address,
                        rssi = result.rssi,
                    )
                )
            }

            override fun onScanFailed(errorCode: Int) {
                close(IllegalStateException("BLE scan failed with code $errorCode"))
            }
        }

        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        scanner.startScan(null, settings, callback)

        awaitClose { scanner.stopScan(callback) }
    }
}
