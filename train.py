#!/usr/bin/env python3
"""
This is a handwriting recorder/trainer for MetaWear sensor.
"""

import argparse
from time import sleep

from mbientlab.metawear import *
from mbientlab.warble import *


def first_metawear_address(wait_seconds=5.0):
    address = None
    discovery = Event()

    def callback_discovered(result):
        nonlocal address
        if result.has_service_uuid(MetaWear.GATT_SERVICE):
            # grab first discovered device
            address = result.mac
            discovery.set()

    BleScanner.set_handler(callback_discovered)
    BleScanner.start()
    no_timeout = discovery.wait(wait_seconds)
    BleScanner.stop()
    return address if no_timeout else None


def list_devices(wait_seconds=5.0):
    printed = set()

    def callback_discovered(result):
        if result.has_service_uuid(MetaWear.GATT_SERVICE):
            mac = result.mac
            if mac not in printed:
                print('Found {} ({})'.format(result.name, mac))
                printed.add(mac)

    BleScanner.set_handler(callback_discovered)
    BleScanner.start()
    sleep(wait_seconds)
    BleScanner.stop()


def record_and_train(mac_address: str):
    samples = record(mac_address)
    text = input('Write reference text press ENTER\n')


def record(mac_address) -> list:
    samples = []

    def data_handler(ctx, data):
        nonlocal samples
        parsed = parse_value(data)
        samples.append((parsed.x, parsed.y, parsed.z))

    callback = FnVoid_VoidP_DataP(data_handler)

    device = MetaWear(mac_address)
    try:
        device.connect()
    except WarbleException:
        print('Failed to connect to device {}'.format(mac_address))
        sys.exit(1)

    libmetawear.mbl_mw_settings_set_connection_parameters(device.board, 7.5, 7.5, 0, 6000)
    libmetawear.mbl_mw_acc_set_odr(device.board, 100.0)
    libmetawear.mbl_mw_acc_set_range(device.board, 2.0)
    libmetawear.mbl_mw_acc_write_acceleration_config(device.board)

    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(device.board)
    libmetawear.mbl_mw_datasignal_subscribe(signal, None, callback)
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(device.board)
    libmetawear.mbl_mw_acc_start(device.board)

    input('Write cursive text and press ENTER\n')

    libmetawear.mbl_mw_acc_stop(device.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(device.board)
    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(signal)
    libmetawear.mbl_mw_debug_disconnect(device.board)

    print('Got {} samples'.format(len(samples)))

    return samples


def main():
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)
    parser.add_argument('-l', '--list', action='store_true', help='List devices')
    parser.add_argument('-r', '--recognize', metavar='MAC_ADDRESS', help='Recognize data from MAC_ADDRESS')
    parser.add_argument('-t', '--train', metavar='MAC_ADDRESS', help='Record data from MAC_ADDRESS and train')
    args = parser.parse_args()

    if args.list:
        list_devices()
    elif args.train:
        record_and_train(args.train)


if __name__ == '__main__':
    main()
