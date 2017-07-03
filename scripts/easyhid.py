#!/usr/bin/env python
# Copyright 2017 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

import cffi

ffi = cffi.FFI()
ffi.cdef("""
struct hid_device_info {
    char *path;
    unsigned short vendor_id;
    unsigned short product_id;
    wchar_t *serial_number;
    unsigned short release_number;
    wchar_t *manufacturer_string;
    wchar_t *product_string;
    unsigned short usage_page;
    unsigned short usage;
    int interface_number;
    struct hid_device_info *next;
};
typedef struct hid_device_ hid_device;

int hid_init(void);
int hid_exit(void);
struct hid_device_info* hid_enumerate(unsigned short, unsigned short);
void hid_free_enumeration (struct hid_device_info *devs);
hid_device* hid_open (unsigned short vendor_id, unsigned short product_id, const wchar_t *serial_number);
hid_device* hid_open_path (const char *path);
int hid_write (hid_device *device, const unsigned char *data, size_t length);
int hid_read_timeout (hid_device *dev, unsigned char *data, size_t length, int milliseconds);
int hid_read (hid_device *device, unsigned char *data, size_t length);
int hid_set_nonblocking (hid_device *device, int nonblock);
int hid_send_feature_report (hid_device *device, const unsigned char *data, size_t length);
int hid_get_feature_report (hid_device *device, unsigned char *data, size_t length);
void hid_close (hid_device *device);
int hid_get_manufacturer_string (hid_device *device, wchar_t *string, size_t maxlen);
int hid_get_product_string (hid_device *device, wchar_t *string, size_t maxlen);
int hid_get_serial_number_string (hid_device *device, wchar_t *string, size_t maxlen);
int hid_get_indexed_string (hid_device *device, int string_index, wchar_t *string, size_t maxlen);
const wchar_t* hid_error (hid_device *device);
""")

hidapi = ffi.dlopen("libhidapi-libusb.so")

class HIDException(Exception):
    pass

# TODO: Would like to save the device info with the device, but there's not
# a guaranteed way to get it from hidapi
class Device:
    def __init__(self, dev, info=None):
        if dev == None:
            raise HIDException("None value for HID Device")
        self.dev = dev
        self.info = info

    def __del__(self):
        self.close()

    def write(self, data, report_id=0):
        """
        Writes `bytes` to the hid device.
        """
        write_data = bytearray([report_id]) + bytearray(data)
        cdata = ffi.new("const unsigned char[]", bytes(write_data))
        num_written = hidapi.hid_write(self.dev, cdata, len(write_data))
        if num_written < 0:
            raise HIDException()
        else:
            return num_written

    def read(self, size=64, timeout=None):
        """
        Read from the hid device. Returns bytes read or None if no bytes read.
        size: number of bytes to read
        timeout: length to wait in milliseconds
        """
        data = [0] * size
        cdata = ffi.new("unsigned char[]", data)
        bytes_read = 0

        if timeout == None:
            bytes_read = hidapi.hid_read(self.dev, cdata, len(cdata))
        else:
            bytes_read = hidapi.hid_read_timeout(self.dev, cdata, len(cdata), timeout)

        if bytes_read < 0:
            raise HIDException(dev.get_error())
        elif bytes_read == 0:
            return None
        else:
            return bytearray(cdata)

    def set_nonblocking(self, enable_nonblocking):
        if type(enable_nonblocking) != bool:
            raise TypeError
        hidapi.hid_set_nonblocking(self.dev, enable_nonblocking)

    def is_connected(self):
        err = hidapi.hid_read_timeout(self.dev, ffi.NULL, 0, 0)
        if err == -1:
            return False
        else:
            return True


# int hid_set_nonblocking (hid_device *device, int nonblock);
# int hid_send_feature_report (hid_device *device, const unsigned char *data, size_t length);
    # def send_feature_report(self, data):
    #     cdata = ffi.new("const unsigned char[]", data)
    #     hidapi.hid_send_feature_report(self.dev, cdata, length)
    #     pass

    # def get_feature_report(self, size=64):
    #     hid_data = bytes([report_id]) + bytes(data)
    #     cdata = ffi.new("unsigned char[]", data)
    #     hidapi.hid_send_feature_report(self.dev, cdata, length)
    #     pass

    def get_error(self):
        err_str = hidapi.hid_error(self.dev)
        if err_str == ffi.NULL:
            return None
        else:
            return ffi.string(err_str)

    def close(self):
        """
        Closes the hid device
        """
        hidapi.hid_close(self.dev)

    def _get_prod_string_common(self, hid_fn):
        max_len = 128
        str_buf = ffi.new("wchar_t[]", bytearray(max_len).decode('utf-8'))
        ret = hid_fn(self.dev, str_buf, max_len)
        if ret < 0:
            raise HIDException(dev.get_error())
        else:
            assert(ret == 0)
            return ffi.string(str_buf)

    def get_manufacture_string(self):
        """
        Get the manufacturer string of the device from its device descriptor
        """
        return self._get_prod_string_common(hidapi.hid_get_manufacturer_string)

    def get_product_string(self):
        """
        Get the product string of the device from its device descriptor
        """
        return self._get_prod_string_common(hidapi.hid_get_product_string)

    def get_serial_number(self):
        """
        Get the serial number string of the device from its device descriptor
        """
        return self._get_prod_string_common(hidapi.hid_get_serial_number_string)

    def get_indexed_string(self, index):
        """
        Get the string with the given index from the device
        """
        max_len = 128
        str_buf = ffi.new("wchar_t[]", str(bytearray(max_len)))
        ret = hidapi.hid_get_indexed_string(self.dev, index, str_buf, max_len)

        if ret < 0:
            raise HIDException(dev.get_error())
        elif ret == 0:
            return None
        else:
            return ffi.string(str_buf).encode('utf-8')


class DeviceInfo:
    """
    Python object that contains the values of the hidapi `hid_device_info` struct.
    Fields:
    path -> bytes
    vendor_id -> int
    product_id -> int
    release_number -> int
    manufacturer_string -> str
    product_string -> str
    serial_number -> str
    usage_page = cdata.usage_page
    usage = cdata.usage
    interface_number = cdata.interface_number
    """
    # def __init__(self, cdata):
    def __init__(self, cdata):
        """
        Creates a
        """
        if cdata == ffi.NULL:
            raise TypeError
        self.path = self._string(cdata.path)
        self.vendor_id = cdata.vendor_id
        self.product_id = cdata.product_id
        self.release_number = cdata.release_number
        self.manufacturer_string = self._string(cdata.manufacturer_string)
        self.product_string = self._string(cdata.product_string)
        self.serial_number = self._string(cdata.serial_number)
        self.usage_page = cdata.usage_page
        self.usage = cdata.usage
        self.interface_number = cdata.interface_number

    def _string(self, val):
        if val == ffi.NULL:
            return None

        new_val = ffi.string(val)
        if type(new_val) == bytes or type(new_val) == bytearray:
            return new_val.decode("utf-8")
        else:
            return new_val


    def description(self):
        return \
"""DeviceInfo {{
    path = "{}",
    vid:pid = {:x}:{:x},
    manufacturer = "{}",
    product = "{}",
    serial = "{}",
    release_number = {},
    usage_page = {},
    usage = {},
    interface_number = {}
}}""".format(self.path,
           self.vendor_id,
           self.product_id,
           self.manufacturer_string,
           self.product_string,
           self.serial_number,
           self.release_number,
           self.usage_page,
           self.usage,
           self.interface_number
        )

def hid_enumerate(vendor_id=0, product_id=0):
    """
    Enumerates all the hid devices for VID:PID. Returns a list of `DeviceInfo`.
    If vid is 0, then match any vendor id. Similarly, if pid is 0, match any
    product id. If both are zero, enumerate all HID devices.
    """
    start = hidapi.hid_enumerate(vendor_id, product_id)
    result = []
    cur = ffi.new("struct hid_device_info*");
    cur = start

    # Copy everything into python list
    while cur != ffi.NULL:
        result.append(DeviceInfo(cur))
        cur = cur.next

    # Free the C memory
    hidapi.hid_free_enumeration(start)

    return result

def hid_open_path(path):
    """
    Opens a device with the given path byte string. Returns a `Device`.
    """
    path = path.encode('utf-8')
    dev = hidapi.hid_open_path(path)
    if dev:
        return Device(dev)
    else:
        None

def hid_open(vendor_id, product_id, serial=None):
    """
    """
    if serial == None:
        serial = ffi.NULL
    else:
        if type(serial) == bytes or type(serial) == bytearray:
            serial = serial.decode('utf-8')
        serial = ffi.new("wchar_t[]", serial)
    dev = hidapi.hid_open(vendor_id, product_id, serial)
    if dev:
        return Device(dev)
    else:
        None

if __name__ == "__main__":
    # Examples
    from easyhid import hid_enumerate, hid_open, hid_open_path

    # enumerate all hid devices with VID:PID = 046D:C52B (Logitech USB Receiver)
    dev_info_list = hid_enumerate(0x046d, 0xC52b)

    # enumerate all hid devices with VID 046D (Logitech)
    dev_info_list = hid_enumerate(vendor_id=0x046d)

    # enumerate all hid devices with PID C52B
    dev_info_list = hid_enumerate(product_id=0xc52b)

    # enumerate all hid devices that match any VID and PID
    dev_info_list = hid_enumerate()

    target_device_path = None
    # Print the list of device info, and look for a specific device
    for info in dev_info_list:
        if info.interface_number == 3 and info.vendor_id == 0x6666:
            target_device_path = info.path
        print(info)

    # # Then we can open the HID device from its path
    # device = hid_open_path(target_device_path)

    # Alternatively open first device with the specified vid, pid and option
    # serial number
    another_device = hid_open(0x6666, 0x1111, serial="0.1234")

    another_device.set_nonblocking(True)

    # write bytes to the corresponding HID endpoint
    device.write(bytes([0, 1, 2, 3, 4]))
    # read bytes from the corresponding HID endpoint
    print(device.read())
