# Tested device and limits

The recovery method was exercised on one G50 learning tablet:

| Property | Observation |
| --- | --- |
| Android | 9 / API 28 |
| Platform | Unisoc / Spreadtrum SP9863A, ARM64 |
| Normal Home | `com.android.launcher3/.Launcher` |
| Firmware learning Home | `com.qi.studycomputer.launcher/.activity.LaunchActivity` |
| Boot override property | `ro.jlink.component_name` references the learning launcher |
| Bootloader | Reported locked; no unlock or flash performed |

The firmware advertised inconsistent hardware capacities. The physical display and block-device observations differed from its About screen claims. Treat such claims as unverified rather than choosing software or flash images from them.

Selecting Launcher3 restored normal Android access. Disabling or uninstalling the learning launcher for user 0 did not persist through reboot: the firmware restored it. The normal Home selection was restored again on 2026-10-16. Termux and the desktop files remained installed.

No private device serial, original vendor APK, account information or device backup is included here. This is an empirical case study, not a claim that all G50 tablets use the same board or firmware.
