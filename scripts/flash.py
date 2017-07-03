#!/usr/bin/env python
# Copyright 2017 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import print_function, division

import intelhex
import argparse

import time, math, sys
import boot, easyhid

parser = argparse.ArgumentParser(description='Flashing script for xusb-boot bootloader')
parser.add_argument('-f', dest='hex_file', type=str, action='store', default=None,
                    help='The hexfile to flash'),
parser.add_argument('-d', dest='id', action='store', default=None,
                    metavar="VID:PID",
                    help='The VID:PID pair of the device to flash')
parser.add_argument('-s', dest='serial', type=str, default=None,
                    help='Serial number of the USB device to flash.')
parser.add_argument('-l', dest='listing', const=True, default=False, action='store_const',
                    help='If this flag is given, list the available devices')
parser.add_argument('-p', dest='path', type=str, default=None, action='store',
                    help='The device port path. This value can be used to identify a '
                    ' device if it does not have a serial number. This value '
                    'is not static and may change if the device is reconnected')
parser.add_argument('-v', '--version', action='version',
        version='Version: {}.{}'.format(boot.VERSION_MAJOR, boot.VERSION_MINOR))


class Progress:
    def __init__(self, total=100, bar_size=40):
        self.bar_size = bar_size
        self.total = total

    def start(self):
        self.start_time = time.time()
        self.update(0)

    def update(self, amount_done):
        cur_len = int(math.ceil((amount_done / self.total) * self.bar_size))
        pad_len = self.bar_size - cur_len
        duration = time.time() - self.start_time
        print('\r[{}{}] {:.1f}% ({:.1f}s)'.format(
            '#'*cur_len,
            ' '*pad_len,
            (amount_done / self.total) * 100,
            duration
        ), end="")
        sys.stdout.flush()

    def done(self):
        self.update(self.total)
        print()


def print_device_info(device, device_info, boot_info):
    print("Found device {:x}:{:x}  {} - {}".format(
            device_info.vendor_id,
            device_info.product_id,
            device.get_manufacture_string(),
            device.get_product_string(),
    ))
    serial_str = device.get_serial_number()
    if serial_str:
        print("Serial: ", serial_str)
    print("USB port info", device_info.path)
    print("Bootloader Version: {}.{}".format(boot_info.major, boot_info.minor))
    print("MCU: ", boot_info.mcu)
    print("flash size: ", boot_info.flash_size)
    print("page size: ", boot_info.page_size)

def write_hexfile(device, hexfile, boot_info):
    page_size = boot_info.page_size
    flash_size = boot_info.flash_size
    flash_end = boot_info.flash_size-1
    with open(hexfile) as f:
        ihex = intelhex.IntelHex(f)
        ihex.padding = 0xff
        start = 0
        end = int(math.ceil(ihex.maxaddr() / page_size)) * page_size
        if end > flash_size:
            raise boot.BootloaderException("Hex file to large for flash size. Got {}"
                    " maximum is {}".format(ihex.maxaddr(), flash_size))

        hex_data = ihex.tobinarray(0, flash_end)
        hex_crc = boot.xmega_nvm_crc(hex_data)

        # Write the page region in the hex file and print a progress bar every
        # time we write a page
        print("Writing hex file '{}' ({} bytes) (CRC: 0x{:06x})".format(
            args.hex_file, end, hex_crc))
        prog = Progress(total=end, bar_size=50)
        boot.erase(device) # must erase before we can write
        prog.start()
        boot.write_start(device, start, end) # tell mcu the region to write
        for i in range(start, end, page_size): # handle one page at a time
            data = bytearray(hex_data[i:i+page_size])
            boot.write_page(device, data, page_size)
            prog.update(i)
        prog.done()

        app_crc, boot_crc = boot.crc(device)


        if app_crc != hex_crc:
            print()
            print("Write FAILED! CRC mismatch")
            print("0x{:06x} != 0x{:06x} ".format(app_crc, hex_crc))
            exit(5)
        else:
            print("Write successful, CRC: 0x{:06x}".format(app_crc))
            print("Reseting mcu ...")
            boot.reset(device)
            exit(0)


if __name__ == "__main__":
    args = parser.parse_args()

    # Get the device id which the hex will be flased to.
    vid = 0
    pid = 0
    if args.id != None:
        try:
            vid, pid = args.id.split(":")
            vid = int(vid, base=16)
            pid = int(pid, base=16)
            if vid > 0xFFFF or pid > 0xFFFF:
                raise Exception
        except:
            print("bad VID:PID pair: '{}'".format(args.id))
            parser.exit(1)

    has_specific_device = vid or pid or args.path or args.serial
    if not (has_specific_device or args.listing or args.hex_file):
        parser.print_help()


    device = None
    device_info = None
    boot_info = None

    if has_specific_device:
        if args.path:
            device = easyhid.hid_open_path(args.path)
        elif (vid and pid):
            device = easyhid.hid_open(vid, pid, serial=args.serial)
        elif args.serial:
            for info in easyhid.hid_enumerate():
                if info.serial_number == args.serial:
                    vid = info.vendor_id
                    pid = info.product_id
                    device = easyhid.hid_open(vid,pid, serial=args.serial)
                    break;
    else:
        # no information was given about what device to use
        # So here were scan through the devices and look at only those that
        # use know default values.
        #
        # If we are listing devices, then print each matching device to stdout.
        # If not, then select the first matching device
        dev_info_list = easyhid.hid_enumerate(vid, pid)
        for info in dev_info_list:
            is_match = info.manufacturer_string == boot.DEFAULT_MANUFACTUER and \
                    info.product_string == boot.DEFAULT_PRODUCT
            is_match = is_match or (info.vendor_id == boot.DEFAULT_VID and \
                    info.product_id == boot.DEFAULT_PID)
            if is_match:
                if not args.listing:
                    # If we have a hexfile,
                    device = easyhid.hid_open_path(info.path)
                    device_info = info
                    break
                else:
                    hid_dev = easyhid.hid_open_path(info.path)
                    boot_info = boot.get_boot_info(hid_dev)
                    print_device_info(hid_dev, info, boot_info)
                    print()

    if device_info == None:
        for info in easyhid.hid_enumerate():
            if args.path == info.path:
                device_info = info
                break
            if args.serial and info.serial_number != args.serial:
                continue
            if vid and (info.vendor_id != vid):
                continue
            if pid and (info.product_id != pid):
                continue
            device_info = info
            break;

    # Print the info of the device we wound
    if device != None:
        boot_info = boot.get_boot_info(device)
        print_device_info(device, device_info, boot_info)

    # If we're not programming a hex file, then nothing left to do
    if args.hex_file == None:
        exit(0)

    if device == None:
        # Couldn't find a device to program the hex file to
        print("Couldn't find any device to program")
        exit(2)
    else:
        write_hexfile(device, args.hex_file, boot_info)
