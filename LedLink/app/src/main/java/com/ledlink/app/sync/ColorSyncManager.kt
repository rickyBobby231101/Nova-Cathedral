package com.ledlink.app.sync

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.ParcelUuid
import com.ledlink.app.model.LedColorState
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import java.util.UUID

/**
 * "Sync mode": every phone in the same session continuously advertises its current LED color
 * as a small BLE advertisement (manufacturer data), and listens for the same advertisement
 * from other nearby phones. When one phone's color changes, everyone else picks it up over
 * the air within about a second and mirrors it to their own connected LED device.
 *
 * This is real RF sensing/communication (standard BLE advertising + scanning, no pairing, no
 * internet) rather than a gimmick, but it only works between phones running this app — it
 * cannot join or synchronize with unrelated closed-hardware devices (see README).
 *
 * A "session" is just a single byte 0-255 the user picks so multiple independent groups
 * nearby don't mirror each other's colors.
 */
class ColorSyncManager(context: Context) {

    companion object {
        // Randomly-generated 128-bit UUID reserved for this app's sync advertisements.
        val SYNC_SERVICE_UUID: UUID = UUID.fromString("6e12c1a0-2f3b-4e9d-9a2f-7b1d4c8e5a10")
        private const val MANUFACTURER_ID = 0xFFFF // Unassigned/testing manufacturer ID.
    }

    private val adapter: BluetoothAdapter? =
        (context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager)?.adapter

    private var advertiseCallback: AdvertiseCallback? = null

    @SuppressLint("MissingPermission")
    fun startAdvertising(sessionId: Int, color: LedColorState) {
        val advertiser = adapter?.bluetoothLeAdvertiser ?: return
        stopAdvertising()

        val payload = byteArrayOf(
            sessionId.toByte(),
            color.red.toByte(),
            color.green.toByte(),
            color.blue.toByte(),
            if (color.on) 1 else 0,
        )

        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .setConnectable(false)
            .build()

        val data = AdvertiseData.Builder()
            .addServiceUuid(ParcelUuid(SYNC_SERVICE_UUID))
            .addManufacturerData(MANUFACTURER_ID, payload)
            .build()

        val callback = object : AdvertiseCallback() {}
        advertiseCallback = callback
        advertiser.startAdvertising(settings, data, callback)
    }

    @SuppressLint("MissingPermission")
    fun stopAdvertising() {
        val advertiser = adapter?.bluetoothLeAdvertiser ?: return
        advertiseCallback?.let { advertiser.stopAdvertising(it) }
        advertiseCallback = null
    }

    /** Emits colors broadcast by other phones in the same [sessionId]. */
    @SuppressLint("MissingPermission")
    fun peerColors(sessionId: Int): Flow<LedColorState> = callbackFlow {
        val scanner = adapter?.bluetoothLeScanner
        if (scanner == null) {
            close(IllegalStateException("Bluetooth is not available or disabled"))
            return@callbackFlow
        }

        val callback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                val bytes = result.scanRecord?.getManufacturerSpecificData(MANUFACTURER_ID) ?: return
                if (bytes.size < 5) return
                if (bytes[0].toInt() and 0xFF != sessionId) return
                trySend(
                    LedColorState(
                        red = bytes[1].toInt() and 0xFF,
                        green = bytes[2].toInt() and 0xFF,
                        blue = bytes[3].toInt() and 0xFF,
                        on = bytes[4].toInt() != 0,
                    )
                )
            }

            override fun onScanFailed(errorCode: Int) {
                close(IllegalStateException("Sync scan failed with code $errorCode"))
            }
        }

        val filter = android.bluetooth.le.ScanFilter.Builder()
            .setServiceUuid(ParcelUuid(SYNC_SERVICE_UUID))
            .build()
        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        scanner.startScan(listOf(filter), settings, callback)

        awaitClose { scanner.stopScan(callback) }
    }
}
