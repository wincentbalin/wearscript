#!/usr/bin/env python
"""
This is a handwriting recorder/trainer for MetaWear sensor.
"""

from mbientlab.warble import *
from mbientlab.metawear import *
from threading import Event


e = Event()
address = None


def device_discover_task(result):
    global address
    if result.has_service_uuid(MetaWear.GATT_SERVICE):
        # grab first discovered device
        address = result.mac
        e.set()


def main():
    print('Scanning for device...')
    BleScanner.set_handler(device_discover_task)
    BleScanner.start()
    e.wait()
    BleScanner.stop()
    print('MetaWear MAC address: {}'.format(address))


if __name__ == '__main__':
    main()
