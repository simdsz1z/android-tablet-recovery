# Android Tablet Recovery

[![Checks](https://github.com/simdsz1z/android-tablet-recovery/actions/workflows/checks.yml/badge.svg)](https://github.com/simdsz1z/android-tablet-recovery/actions/workflows/checks.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Restore access to a normal Android Home screen on older tablets that boot into a restricted learning launcher. A small Python tool uses an **already authorized ADB connection**, backs up the current Home selection, then opens the installed Android launcher.

Created during recovery of a G50 learning tablet running Android 9. The same tablet later returned to its children's Home screen; restoring the Home selection recovered access without erasing its Linux desktop or files.

**[Quick start](#quick-start)** · [Recovery guide](docs/recovery-guide.md) · [Device notes](docs/tested-device.md) · [Linux desktop project](https://github.com/simdsz1z/linux-on-old-android)

## What it does

| Feature | Behavior |
| --- | --- |
| Diagnose | Read Android version, model, current Home and known firmware override property |
| Back up | Save a small private record of the current Home selection |
| Recover | Select and open an existing normal Android launcher |
| Restore | Reapply Home from a backup made for the same connected device |
| Open Settings | Request Android's installed Settings activity |

This is **launcher recovery, not a firmware replacement**. It does not flash partitions, unlock the bootloader, root the device, remove applications, erase data, bypass device ownership or defeat administrator policy. Boot-time firmware overrides can restore the learning launcher again.

## Requirements

- A tablet you own or are authorized to administer, with USB debugging enabled and the computer authorized.
- Python 3.9+ and official [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools).
- An installed normal launcher. The default is `com.android.launcher3/.Launcher`; use `--launcher` for another component.
- Android user **0**. Tested on Android **9 / API 28**; other firmware versions are unverified.

## Quick start

```sh
git clone https://github.com/simdsz1z/android-tablet-recovery.git
cd android-tablet-recovery
python android_recovery.py doctor
python android_recovery.py recover
```

The recovery command creates a private backup before changing Home. Keep its printed path for rollback. If the launcher is absent or Android rejects the command, the tool stops rather than removing the learning app.

ADB outside your PATH:

```sh
python android_recovery.py --adb "/path/to/platform-tools/adb" recover
```

For Windows, point `--adb` at `adb.exe`. When several devices are connected, select one explicitly:

```sh
python android_recovery.py --serial YOUR_DEVICE_ID recover
```

## Backup and rollback

```sh
python android_recovery.py backup
python android_recovery.py restore state/YOUR_BACKUP.json
python android_recovery.py settings
```

Backups contain a device identifier and stay in ignored `state/` storage. A backup restores only the **Home selection**; it is not a full device or app-data backup. Restoring also backs up the current selection first. Do not upload state files, package inventories or personal screenshots to issues.

## If the children's Home returns

Reconnect USB, authorize the same computer if prompted, and run `recover` again. On the tested G50, the firmware names its learning launcher in `ro.jlink.component_name` and re-enables it at boot. Changing the default launcher is therefore temporary. Disabling or removing the learning app was previously tried on that device and did not survive reboot; this tool deliberately avoids repeating those changes.

Your apps and Linux installation may still be present. Recover Android Home first, then open Termux and your desktop. See [Linux on Old Android](https://github.com/simdsz1z/linux-on-old-android) for setup and restart recovery.

For a visible Never sleep control, see the separate [Screen sleep app](https://github.com/simdsz1z/screen-sleep).

## Validation

- **Device verified:** selecting Launcher3 and opening it through authorized ADB on the G50; Linux files and applications retained; recovery repeated after the learning launcher returned.
- **Automated:** ambiguous and unauthorized connections, backup-before-change behavior, rollback device matching, command rejection and component input validation.
- **Not established:** a permanent firmware fix, a universal launcher component, support for every learning tablet, or a native Linux boot port.

Run checks without a tablet:

```sh
python -m unittest discover -s tests -v
```

The Python wrapper generalizes the ADB commands used on the tablet. Its automated checks use simulated device responses; they are not tests across real Android models.

## Contributing

Open an issue with your Android version, model, command used and a redacted error. Do not include serial numbers or private backups. Changes should preserve backups, reject ambiguous devices and avoid destructive recovery. Original scripts and documentation are MIT licensed; Android, Termux and firmware remain subject to their respective licenses.
