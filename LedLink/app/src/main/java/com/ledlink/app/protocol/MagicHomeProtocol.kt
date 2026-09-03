package com.ledlink.app.protocol

import com.ledlink.app.model.LedColorState
import java.util.UUID

/**
 * Byte-level command builder for the "Magic Home / Triones / Zengge" BLE protocol.
 *
 * This is the de-facto standard used by a very large share of cheap generic BLE RGB(W)
 * strip/bulb controllers sold under dozens of storefront names. It is NOT an official spec —
 * there is no single vendor to point to — it comes from years of community reverse-engineering
 * (the "flux_led" project documents the WiFi sibling of the same command bytes). Some clone
 * controllers use a slightly different service/characteristic UUID or a longer checksummed
 * frame; if a device connects but ignores commands, use a generic BLE tool (e.g. nRF Connect)
 * to read its GATT table and adjust SERVICE_UUID / WRITE_CHARACTERISTIC_UUID below.
 */
object MagicHomeProtocol {

    val SERVICE_UUID: UUID = UUID.fromString("0000ffd5-0000-1000-8000-00805f9b34fb")
    val WRITE_CHARACTERISTIC_UUID: UUID = UUID.fromString("0000ffd9-0000-1000-8000-00805f9b34fb")

    /** Sets RGB color. White channel is left at 0 since most cheap strips are RGB-only. */
    fun setColor(state: LedColorState): ByteArray = byteArrayOf(
        0x56,
        state.red.toByte(),
        state.green.toByte(),
        state.blue.toByte(),
        0x00,
        0xF0.toByte(),
        0xAA.toByte(),
    )

    fun setPower(on: Boolean): ByteArray =
        if (on) byteArrayOf(0xCC.toByte(), 0x23, 0x33) else byteArrayOf(0xCC.toByte(), 0x24, 0x33)
}
