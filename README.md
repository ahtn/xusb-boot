# xusb-boot

A simple bootloader for the xmega that uses a raw HID interface so it can
work without drivers. It uses the internal RC oscillator for the USB clock.
It also allows for application code to write to flash using the functions
given in `spm_interface.h`. Released under MIT software license.

## Installation instructions and dependencies

### Dependencies
To use the python flashing script you python,
[hidapi](http://www.signal11.us/oss/hidapi/) library. The python libraries
`cffi` and `intelhex` are also needed. To install them use:

```
pip install cffi intelhex
```

### Building

To build the bootloader run:

```
make
```

The commands `make program` and `make program-fuses` can be used to flash the
hex file and configure the fuses. For more information read the makefile.


## Flashing a hex file with the bootloader

To use the bootloader, run:

```
./scripts/flash.py -f hex_file
```

It will search for the first device that matches, and attempt to program it.

To program a specific device instead use:

```
./scripts/flash.py -d VID:PID -s "<serial_num>" -f hex_file
```

To list available devices use

```
./scripts/flash.py -l
```

For more help use:

```
./scripts/flash.py -h
```

## Ways to enter the bootloader

On power up the bootloader will by default run the application code if present.
There are 3 ways to enter the bootloader:

* Unprogrammed flash
* Reset button
* Software reset into bootloader

### Enter bootloader by unprogrammed flash

If the flash at address 0 is `0xffff`, then the bootloader assumes that
the device is unprogrammed and runs the bootloader code.

### Enter bootloader with reset button

The bootloader can also be run by pressing the reset button (bring RST pin low).
The bootloader will then attempt to establish a USB connection. If it can't,
it will reset and enter the application code if present. If no application code
is present then it will keep reseting until it can establish a USB connection.

To determine if a USB connection is present, the bootloader has 2 strategies
available.

1. An IO pin that monitors VBUS. The pin can be set with `CHECK_PIN` and
   `CHECK_PORT` in `config.h`.
2. Checking for USB SOF packets. If no SOF packet is received before
   `WATCH_DOG_PERIOD` expires, then the bootloader will reset into the
   application section. The default value is to wait 2s before rebooting.

The IO pin strategy has the advantage of being able to reset instantly when
no USB connection is present, but it requires an extra IO pin.

If the reset button is pressed again while the bootloader is running then
the bootloader will reset into the application section. This allows you to
reset the xmega while a USB connection is present by pressing the reset button
twice.

### Enter the bootloader from software

To enter the bootloader from software
```
#define BOOTLOADER_MAGIC 0x97e1e28e
#define BOOTLOADER_FLAG_ADDRESS 0x802400

void software_reset(void) {
    // use xmega software reset functionality
    asm volatile("cli\n\t"          // disable interrupts
                "ldi r24, 0xD8\n\t" // value to write to CCP
                "ldi r25, 0x01\n\t" // value to write to SWRST
                "ldi r30, 0x78\n\t"  // base address of RST peripheral
                "ldi r31, 0\n\t"
                "out __CCP__, r24\n\t"
                "std Z+1, r25\n\t"  // +1 is the offset of RST.CTRL
                ::); // no clobber list because we don't return
}

void reset_to_bootloader(void) {
    *((uint32_t*)BOOTLOADER_FLAG_ADDRESS) = BOOTLOADER_MAGIC;
    software_reset();
}
```

## SRAM wiping

At power up the bootloader fills SRAM with the value `0xCC`. This is done
to prevent newly loaded firmware from extracting SRAM data from the previously
loaded firmware. It can also serve as a debugging aid.

The only values that will not be filled with `0xCC` is the 4 bytes at
`BOOTLOADER_FLAG_ADDRESS` which are used to pass data to and from the
bootloader when the device is reset. The data at this location is still cleared
before the application code is run, just not necessarily to the value 0xCC.

## Access SPM instructions from code running in the application section

Currently the bootloader exposes the following functions:

```
// Erase the application page at the given byte address. The address can point
// anywhere inside the page.
// SPM interface table offset 0
void erase_application_page(uint32_t address);

// This function is used to write a page to the given byte address. The address
// can point anywhere inside the page.
// SPM interface table offset 1
void write_application_page(uint8_t *data, uint32_t address);
```

They are store in a jump table starting in the last 32 bytes of the bootloader.
Remember to call these functions using their word address if referenced directly
from C. For example

```
// How to use the spm interface functions in C from the application section.
// Example for ATxmega32a4u
#define BOOTLOADER_END (0x9000)
#define SPM_FN_TABLE (BOOTLOADER_END - 32)
#define BYTE_TO_WORD_ADDR(x) ((x) / 2)

// The word addresses of the functions
#define SPM_ERASE_ADDR (BYTE_TO_WORD_ADDR(SPM_FN_TABLE) + 0)
#define SPM_WRITE_ADDR (BYTE_TO_WORD_ADDR(SPM_FN_TABLE) + 1)

typedef void (*spm_erase_fn_t)(uint32_t addr);
typedef void (*spm_write_fn_t)(uint8_t *data, uint32_t addr);

spm_erase_fn_t erase_app_page = (spm_erase_fn_t)(SPM_ERASE_ADDR);
spm_write_fn_t write_app_page = (spm_write_fn_t)(SPM_WRITE_ADDR);

```

## Recover reset flags

For the bootloader to work correctly, it needs to clear some of the flags
in the RST.STATUS register. So to allow the application code to see these flags,
it makes a copy of RST.STATUS register at the address
`BOOTLOADER_FLAG_ADDRESS 0x802400`. Also, if the bootloader itself is reset
while it is running, then `bit 0` at `0x802401` is set.
The application code should still clear the RST.STATUS flags it uses as the
bootloader does not clear all reset flags.

## License

This code is released under the terms of the
[MIT](https://opensource.org/licenses/MIT) software license. See the `LICENSE`
for more information.
