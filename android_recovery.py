#!/usr/bin/env python3
"""Restore a normal Android Home screen through an authorized ADB connection."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import uuid

COMPONENT = re.compile(r'[A-Za-z0-9_.$]+/[A-Za-z0-9_.$]+')
ROOT = Path(__file__).resolve().parent


class RecoveryError(RuntimeError):
    pass


def component(value):
    if not COMPONENT.fullmatch(value):
        raise RecoveryError('Use an Android component such as com.android.launcher3/.Launcher.')
    return value


def parse_home(output):
    for line in reversed(output.splitlines()):
        if COMPONENT.fullmatch(line.strip()):
            if line.strip().startswith('android/') and line.strip().endswith('ResolverActivity'):
                return None
            return line.strip()
    return None


class ADB:
    def __init__(self, executable='adb', serial=None):
        self.executable = shutil.which(executable) or executable
        self.serial = serial

    def run(self, *args):
        try:
            result = subprocess.run([self.executable, *args], capture_output=True, text=True, timeout=30)
        except FileNotFoundError as error:
            raise RecoveryError('ADB not found. Install Android Platform Tools or pass --adb PATH.') from error
        except subprocess.TimeoutExpired as error:
            raise RecoveryError('ADB timed out. Check the USB connection and authorization.') from error
        if result.returncode:
            raise RecoveryError('ADB command failed. Check the connection, authorization and device policy.')
        return result.stdout.strip()

    def connect(self):
        rows = [line.split()[:2] for line in self.run('devices').splitlines()[1:] if line.strip()]
        devices = {row[0]: row[1] for row in rows if len(row) == 2}
        if self.serial:
            if devices.get(self.serial) != 'device':
                raise RecoveryError('The selected device is missing, offline or not authorized. Accept its USB debugging prompt.')
        else:
            ready = [serial for serial, state in devices.items() if state == 'device']
            if len(ready) != 1:
                raise RecoveryError('Connect exactly one authorized device, or pass --serial DEVICE_ID. Use adb devices to inspect connections.')
            self.serial = ready[0]
        return self

    def shell(self, *args):
        output = self.run('-s', self.serial, 'shell', shlex.join(args))
        if re.search(r'(?m)^(?:Error:|SecurityException|java\.lang\..*Exception)', output):
            raise RecoveryError('Android rejected the command. No policy or permission bypass is attempted.')
        return output

    def home(self):
        return parse_home(self.shell('cmd', 'package', 'resolve-activity', '--brief', '--user', '0',
                                     '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME'))


def snapshot(adb, directory):
    data = {'schema': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
            'device_serial': adb.serial, 'user': 0, 'home': adb.home(),
            'model': adb.shell('getprop', 'ro.product.model'),
            'android': adb.shell('getprop', 'ro.build.version.release')}
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8] + '.json')
    with path.open('x', encoding='utf-8') as file:
        json.dump(data, file, indent=2)
        file.write('\n')
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def restore_home(adb, launcher, directory):
    launcher = component(launcher)
    package = launcher.split('/')[0]
    if not adb.shell('pm', 'path', '--user', '0', package).startswith('package:'):
        raise RecoveryError('That launcher is not installed for Android user 0. Nothing was changed.')
    resolved = parse_home(adb.shell('cmd', 'package', 'resolve-activity', '--brief', '--user', '0', '-n', launcher,
                                   '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME'))
    if not resolved:
        raise RecoveryError('Android could not resolve that launcher. Nothing was changed.')
    backup = snapshot(adb, directory)
    print(f'Previous Home saved privately: {backup}')
    result = adb.shell('cmd', 'package', 'set-home-activity', '--user', '0', launcher)
    if 'Success' not in result:
        raise RecoveryError('Android did not confirm the Home change. Keep the backup and inspect the device.')
    if adb.home() != resolved:
        raise RecoveryError('The firmware did not retain the requested Home. Keep the backup; do not retry destructive actions.')
    adb.shell('input', 'keyevent', '224')
    adb.shell('am', 'start', '--user', '0', '-W', '-n', launcher)
    print('Normal Home selected and opened. Firmware may override it after reboot.')
    return backup


def restore_snapshot(adb, path, directory):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema') != 1 or data.get('user') != 0 or data.get('device_serial') != adb.serial:
        raise RecoveryError('Backup does not match this device, user or backup format. Nothing was changed.')
    if not data.get('home'):
        raise RecoveryError('Backup has no resolved Home component. Nothing was changed.')
    return restore_home(adb, data['home'], directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', default='adb', help='ADB executable path')
    parser.add_argument('--serial', help='Select a device when more than one is connected')
    parser.add_argument('--state-dir', type=Path, default=ROOT / 'state', help='Private, local backup directory')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor', help='Read-only connection and firmware summary')
    commands.add_parser('backup', help='Save the current Home selection without changing it')
    recover = commands.add_parser('recover', help='Back up, select and open a normal launcher')
    recover.add_argument('--launcher', default='com.android.launcher3/.Launcher')
    commands.add_parser('settings', help='Open Android Settings, if installed')
    restore = commands.add_parser('restore', help='Restore the Home component from a matching local backup')
    restore.add_argument('backup_file', type=Path)
    args = parser.parse_args()
    try:
        adb = ADB(args.adb, args.serial).connect()
        if args.command == 'doctor':
            print('Authorized ADB connection: ready')
            print('Model:', adb.shell('getprop', 'ro.product.model'))
            print('Android:', adb.shell('getprop', 'ro.build.version.release'))
            print('Home:', adb.home() or 'unresolved')
            override = adb.shell('getprop', 'ro.jlink.component_name')
            if override:
                print('Firmware boot launcher override:', override)
                print('Home changes may need repeating after reboot.')
        elif args.command == 'backup':
            print('Private backup:', snapshot(adb, args.state_dir))
        elif args.command == 'recover':
            restore_home(adb, args.launcher, args.state_dir)
        elif args.command == 'restore':
            restore_snapshot(adb, args.backup_file, args.state_dir)
        elif args.command == 'settings':
            adb.shell('am', 'start', '--user', '0', '-W', '-a', 'android.settings.SETTINGS')
            print('Android Settings requested.')
        return 0
    except (RecoveryError, OSError, ValueError) as error:
        print(f'Could not complete: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
