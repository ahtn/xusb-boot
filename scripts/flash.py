#!/usr/bin/env python
# Copyright 2017 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

from __future__ import print_function, division

import intelhex
import argparse

import time, math, sys
import boot
import easyhid

EXIT_NO_ERROR = 0
EXIT_ARGUMENTS_ERROR = 1
EXIT_OPEN_ERROR = 2
EXIT_CRC_ERROR = 5


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


def print_device_info(device):
    print("Found device {:x}:{:x}  {} - {}".format(
            device.vendor_id,
            device.product_id,
            device.get_manufacture_string(),
            device.get_product_string(),
    ))
    serial_str = device.get_serial_number()
    if serial_str:
        print("Serial: ", serial_str)

    boot_info = boot.get_boot_info(device)
    print("USB port info", device.path)
    print("Bootloader Version: {}.{}".format(boot_info.version_major, boot_info.version_minor))
    print("MCU: ", boot_info.mcu_string)
    print("flash size: ", boot_info.flash_size)
    print("page size: ", boot_info.page_size)

def write_hexfile(device, hexfile):
    boot_info = boot.get_boot_info(device)
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
            print("Write FAILED! CRC mismatch: 0x{:06x} != 0x{:06x} "
                  .format(app_crc, hex_crc), file=sys.stderr)
            exit(EXIT_CRC_ERROR)
        else:
            print("Write successful, CRC: 0x{:06x}".format(app_crc))
            print("Reseting mcu ...")
            boot.reset(device)
            exit(EXIT_NO_ERROR)


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
            print("bad VID:PID pair: '{}'".format(args.id), file=sys.stderr)
            parser.exit(EXIT_ARGUMENTS_ERROR)

    has_specific_device = vid or pid or args.path or args.serial
    if not (has_specific_device or args.listing or args.hex_file):
        parser.print_help()

    if vid == 0 and pid == 0:
        vid = boot.DEFAULT_VID
        pid = boot.DEFAULT_PID


    device = None
    boot_info = None

    devices = easyhid.Enumeration().find(
        vid = vid,
        pid = pid,
        path = args.path,
        serial = args.serial
    )


    if args.listing:
        for dev in devices:
            dev.open()
            print_device_info(dev)
            dev.close()
            print()
        exit(EXIT_NO_ERROR)

    if len(devices) == 0:
        print("Couldn't find device to program", file=sys.stderr)
        exit(EXIT_OPEN_ERROR)

    if len(devices) > 1:
        print("Found {} devices, programing the first one: ".format(len(devices)))

    device = devices[0]
    try:
        device.open()
    except:
        print("Couldn't open the device. Check that device is still connected "
              " and that you have permission to write to it.")
        exit(EXIT_OPEN_ERROR)


    # Print the info of the device we found
    print_device_info(device)

    write_hexfile(device, args.hex_file)
