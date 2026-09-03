package com.ledlink.app.ble

import android.annotation.SuppressLint
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothProfile
import android.content.Context
import com.ledlink.app.model.LedColorState
import com.ledlink.app.protocol.MagicHomeProtocol
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

enum class LedConnectionState { DISCONNECTED, CONNECTING, CONNECTED, READY }

/** Owns the GATT connection to one BLE LED controller and sends it Magic Home protocol frames. */
class BleLedController(private val context: Context) {

    private var gatt: BluetoothGatt? = null
    private var writeCharacteristic: BluetoothGattCharacteristic? = null

    private val _state = MutableStateFlow(LedConnectionState.DISCONNECTED)
    val state: StateFlow<LedConnectionState> = _state

    @SuppressLint("MissingPermission")
    fun connect(device: BluetoothDevice) {
        _state.value = LedConnectionState.CONNECTING
        gatt = device.connectGatt(context, false, object : BluetoothGattCallback() {
            override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
                when (newState) {
                    BluetoothProfile.STATE_CONNECTED -> {
                        _state.value = LedConnectionState.CONNECTED
                        g.discoverServices()
                    }
                    BluetoothProfile.STATE_DISCONNECTED -> {
                        _state.value = LedConnectionState.DISCONNECTED
                        writeCharacteristic = null
                    }
                }
            }

            override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
                val service = g.getService(MagicHomeProtocol.SERVICE_UUID)
                writeCharacteristic = service?.getCharacteristic(MagicHomeProtocol.WRITE_CHARACTERISTIC_UUID)
                _state.value = if (writeCharacteristic != null) {
                    LedConnectionState.READY
                } else {
                    LedConnectionState.CONNECTED
                }
            }
        })
    }

    @SuppressLint("MissingPermission")
    fun disconnect() {
        gatt?.disconnect()
        gatt?.close()
        gatt = null
        writeCharacteristic = null
        _state.value = LedConnectionState.DISCONNECTED
    }

    @SuppressLint("MissingPermission")
    fun sendColor(state: LedColorState) {
        write(MagicHomeProtocol.setColor(state))
    }

    @SuppressLint("MissingPermission")
    fun sendPower(on: Boolean) {
        write(MagicHomeProtocol.setPower(on))
    }

    @SuppressLint("MissingPermission")
    private fun write(bytes: ByteArray) {
        val g = gatt ?: return
        val characteristic = writeCharacteristic ?: return
        characteristic.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
        characteristic.value = bytes
        g.writeCharacteristic(characteristic)
    }
}
