# Recovering access

## When Settings is hidden

USB file-transfer choices are separate from debugging. On the original tablet, the USB page offered charge only, MTP, PTP, MIDI and a virtual CD-ROM; none of those enabled ADB.

If the built-in browser permits APK installation, [Activity Launcher](https://f-droid.org/packages/de.szalkowski.activitylauncher/) can expose installed Settings activities. Open the Android Settings entry, find About tablet, tap Build number seven times, then enable USB debugging in Developer options. Chinese labels commonly include `设置` (Settings), `开发者选项` (Developer options) and `USB 调试` (USB debugging). Firmware can hide or remove these activities; installation of Activity Launcher alone does not guarantee access.

Connect a data-capable USB cable and accept the tablet's debugging authorization prompt. `adb devices` should report `device`. `unauthorized` requires approval on the tablet. MTP alone is not enough. If access is managed by another owner or administrator, use that owner's supported recovery process.

## Choosing a launcher

The project's default component worked on the G50, but launcher packages differ by device. Inspect the installed Home activities rather than guessing:

```sh
adb shell cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.HOME
```

Pass the normal launcher's component to `recover --launcher PACKAGE/ACTIVITY`. If no normal launcher is installed, install a trusted compatible launcher through an available supported channel first. The tool does not download APKs or choose a third-party launcher automatically.

## Firmware restores the old launcher

The default Home setting and the firmware's boot behavior are distinct. A manufacturer can restore its launcher during startup even after a successful Home change. The recovery tool can reopen normal Android for the session, but cannot make a locked firmware stop enforcing its own startup policy.

Do not assume a factory reset removes software in the system image. Do not flash a similarly named tablet's image: a model name does not identify a compatible board, display, storage layout or signing key. This project supplies no flash images or unlock procedure.

## Private state

Each snapshot includes the resolved Home, Android version, model, timestamp, primary user and selected device identifier. It is written before a Home change. Keep it locally. If a command fails after the change, inspect the device and use the backup rather than retrying unrelated destructive actions.

For normal app and document backups, use Android's supported backup/export mechanisms separately. This project's JSON file cannot recover erased data.
