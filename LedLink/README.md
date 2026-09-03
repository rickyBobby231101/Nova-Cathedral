# LedLink

A native Android app for controlling color-changing LED devices over Bluetooth Low Energy
(BLE), plus Govee's cloud API for devices that don't expose an open local protocol, plus a
"Sync" mode that lets multiple phones running this app mirror the same color live.

## What this can and can't control

**Can control:**
- Generic BLE RGB(W) LED strip/bulb controllers — the very common "Magic Home / Triones /
  Zengge" family sold under dozens of storefront names. This is the `Nearby` tab: scan,
  tap a device, connect, drag color sliders.
- Govee smart bulbs/strips that are registered to your Govee account, via Govee's official
  cloud REST API — the `Govee` tab. This needs internet and a free API key from the Govee
  Home app (Profile → Settings → About Us → Apply for API Key). Newer Govee hardware
  encrypts its local BLE traffic per-device, so cloud control is the practical path rather
  than a raw local protocol.

**Can't control — and no phone app can, without extra hardware:**
- The small battery-powered "flashing/blinking" LED balls, buttons, or balloon lights sold
  for parties and festivals. These are a coin cell plus a tiny pre-programmed blink-pattern
  chip with **no radio receiver at all** — there's nothing for any app to talk to. If two of
  them ever looked "in sync," that's either the same manufacturing batch running the same
  timing, or a different, closed hardware system (e.g. professional wristband systems with
  their own RF transmitter/base station) — not something a generic phone app can join.
- 433MHz RF remote-controlled strips (the kind that ship with a small keyfob remote, no
  app). Most phones have no 433MHz radio, so driving these needs an external RF dongle or a
  microcontroller (ESP32/Arduino) bridge — out of scope here, but the codebase is structured
  so a new protocol/transport could be added under `protocol/` if you build a bridge later.

## The "Sync" tab

Rather than trying to reverse-engineer unknown closed festival-toy hardware, Sync mode does
something the phone can actually do: every phone running LedLink and set to the same session
number continuously broadcasts its current color as a small BLE advertisement, and listens
for the same broadcast from nearby phones. Whoever changes color last "wins" and everyone
else mirrors it onto their own connected LED device within about a second. No pairing, no
internet, no server — just BLE advertising + scanning, which is genuine local RF
communication. It links *phones running this app*, not arbitrary festival toys.

## Project structure

```
app/src/main/java/com/ledlink/app/
├── MainActivity.kt          # permissions + bottom-nav shell
├── AppViewModel.kt          # app state, wires UI to BLE/Govee/Sync backends
├── model/LedColorState.kt   # RGB + brightness + power
├── protocol/
│   └── MagicHomeProtocol.kt # byte-level command builder for generic BLE strips
├── ble/
│   ├── BleScanner.kt        # BLE device discovery as a Flow
│   └── BleLedController.kt  # GATT connect + write commands
├── govee/
│   └── GoveeCloudClient.kt  # REST calls to developer-api.govee.com
├── sync/
│   └── ColorSyncManager.kt  # BLE advertise/scan for phone-to-phone color mirroring
└── ui/                      # Jetpack Compose screens (Nearby, Govee, Sync)
```

## Building and running

This was written in an environment without a full Android SDK/emulator available, so it has
**not** been built or run on-device yet — the Gradle scripts, manifest, and Kotlin sources
follow standard, current Android/Compose APIs, but treat it as an unverified first pass and
expect to fix small build issues on first import.

1. Open the `LedLink/` folder in Android Studio (Koala/2024.1 or newer).
2. Let it sync — it will resolve dependencies from Google/Maven Central automatically.
3. Run on a real Android phone (BLE doesn't work in the emulator) on API 26+.
4. Grant the Bluetooth permission prompt on first launch.
5. `Nearby` tab → Scan → tap your LED device once it shows up → drag the color sliders.

If a device connects but the color sliders don't do anything, it's likely using a BLE LED
clone with a different GATT service/characteristic UUID or frame format than the one in
`MagicHomeProtocol.kt`. Install a generic BLE inspector app (e.g. nRF Connect), connect to
the device, note its writable characteristic's UUID, and update `SERVICE_UUID` /
`WRITE_CHARACTERISTIC_UUID` accordingly — the byte frame itself (`0x56 R G B 00 F0 AA`) is
shared by most clones even when the UUIDs differ.

## Command-line build (optional)

```bash
./gradlew assembleDebug
```

requires `ANDROID_HOME` (or `local.properties` → `sdk.dir=`) pointing at an installed
Android SDK with platform 34 and build-tools 34.0.0.
