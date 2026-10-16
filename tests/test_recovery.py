import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import android_recovery as recovery


class Device:
    serial = 'TEST_DEVICE_ONLY'

    def __init__(self):
        self.selected = 'example.learning/.Home'
        self.calls = []
        self.reject = False

    def home(self):
        return self.selected

    def shell(self, *args):
        self.calls.append(args)
        if args[:2] == ('pm', 'path'):
            return 'package:/system/app/Launcher3/Launcher3.apk'
        if 'resolve-activity' in args:
            return args[args.index('-n') + 1]
        if 'set-home-activity' in args:
            if self.reject:
                return 'Failed'
            self.selected = args[-1]
            return 'Success'
        if args[0] == 'getprop':
            return 'TEST'
        return ''


class RecoveryTests(unittest.TestCase):
    def test_nested_activity_name_is_quoted_for_remote_shell(self):
        adb = recovery.ADB(serial='TEST')
        with patch.object(adb, 'run', return_value='') as run:
            adb.shell('am', 'start', '-n', 'example.app/.Main$Inner')
            self.assertEqual(run.call_args.args[-1], "am start -n 'example.app/.Main$Inner'")

    def test_resolver_is_not_treated_as_a_saved_default_home(self):
        self.assertIsNone(recovery.parse_home('android/com.android.internal.app.ResolverActivity'))

    def test_ambiguous_devices_never_selects_arbitrarily(self):
        adb = recovery.ADB()
        with patch.object(adb, 'run', return_value='List of devices attached\nONE device\nTWO device'):
            with self.assertRaises(recovery.RecoveryError):
                adb.connect()

    def test_unauthorized_selected_device_rejected(self):
        adb = recovery.ADB(serial='ONE')
        with patch.object(adb, 'run', return_value='List of devices attached\nONE unauthorized'):
            with self.assertRaises(recovery.RecoveryError):
                adb.connect()

    def test_backup_precedes_change_and_can_restore(self):
        device = Device()
        with tempfile.TemporaryDirectory() as directory:
            original = device.selected
            backup = recovery.restore_home(device, 'com.android.launcher3/.Launcher', directory)
            data = json.loads(backup.read_text())
            self.assertEqual(data['home'], original)
            self.assertEqual(device.selected, 'com.android.launcher3/.Launcher')
            recovery.restore_snapshot(device, backup, directory)
            self.assertEqual(device.selected, original)

    def test_backup_write_failure_prevents_mutation(self):
        device = Device()
        with patch.object(recovery, 'snapshot', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                recovery.restore_home(device, 'com.android.launcher3/.Launcher', '.')
        self.assertFalse(any('set-home-activity' in call for call in device.calls))

    def test_failed_change_does_not_start_activity(self):
        device = Device()
        device.reject = True
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(recovery.RecoveryError):
                recovery.restore_home(device, 'com.android.launcher3/.Launcher', directory)
            self.assertEqual(len(list(Path(directory).glob('*.json'))), 1)
        self.assertFalse(any(call[0] == 'am' for call in device.calls))

    def test_other_device_backup_is_rejected_before_change(self):
        device = Device()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'wrong.json'
            path.write_text(json.dumps({'schema': 1, 'user': 0, 'device_serial': 'OTHER', 'home': 'example.app/.Home'}))
            with self.assertRaises(recovery.RecoveryError):
                recovery.restore_snapshot(device, path, directory)
        self.assertEqual(device.calls, [])

    def test_shell_metacharacters_in_component_rejected(self):
        device = Device()
        with self.assertRaises(recovery.RecoveryError):
            recovery.restore_home(device, 'example.app/.Home;reboot', '.')
        self.assertEqual(device.calls, [])


if __name__ == '__main__':
    unittest.main()
