# Copyright 2017 jem@seethis.link
# Licensed under the MIT license (http://opensource.org/licenses/MIT)

MCU = atxmega32a4u
ARCH = XMEGA
F_CPU = 32000000
F_USB = 48000000

# Target file name (without extension).
TARGET = xusb-boot

# Output format. (can be srec, ihex, binary)
FORMAT = ihex

#######################################################################
#                           config options                            #
#######################################################################

## This flag disables the VBUS check pin that helps the bootloader quickly
## detect if it has a USB connection. If it is disabled it will relie on
## USB SOF packets to detect if a USB connection is present.
# CFLAGS += -DNO_CHECKPIN
# CFLAGS += -DCHECK_PIN=PIN1_bm
# CFLAGS += -DCHECK_PORT=PORTR

## USB vendor and product ID
# CFLAGS += -DUSB_VID=0x6666
# CFLAGS += -DUSB_PID=0xB007
# CFLAGS += -DUSB_DEVICE_VERSION=0x0000  # binary coded decimal value

#######################################################################
#                         programmer options                          #
#######################################################################

AVRDUDE_CMD=avrdude-pdi -C ~/local/etc/avrdude-pdi.conf -c usbasp -p $(AVRDUDE_PART)

#######################################################################
#                            fuse settings                            #
#######################################################################

 # JTAG UID
FUSE0=00
# Watchdog settings
FUSE1=00 # No watch dog
# b6 = BOOTRST, b5 = TOSCSEL, b1:0 = BODPD
FUSE2=BD # (reset to bootloader and use sampled brown out detection sleep mode)
# b4 = RSTDISBL, b3:2 = STARTUPTIME, b1 = WDLOCK, b0 = JTAGEN
FUSE4=FF
# b5:4 = BODACT, b3 = EESAVE, b2:0 = BODLEVEL
FUSE5=D6 # sampled BOD @ 1.8V, preserve EEPROM on chip erase
# FUSE5=DE # sampled BOD @ 1.8V, erase EEPROM on chip erase

LOCKBITS_DEBUG := BF # RW enabled for external programmer
LOCKBITS_RELEASE := BC # RW disabled for external programmer
LOCKBITS = $(LOCKBITS_RELEASE)
program-lock:
	avrdude-pdi -C ~/local/etc/avrdude-pdi.conf -c usbasp -p x32a4 \
		-U lock:w:0x$(LOCKBITS):m \

#######################################################################
#                           compiler setup                            #
#######################################################################

# Object files directory
OBJ_DIR = obj

# Update path
XMEGA_PATH=xusb
VPATH += $(XMEGA_PATH)
INC_PATHS += \

# Include sub makefiles
include $(XMEGA_PATH)/makefile
include $(XMEGA_PATH)/xmega/makefile

 # workaround for bad code generation on avr-gcc on linux (version 6.2.0)
CFLAGS += -fno-jump-tables

# we don't want to use interrupts in the bootloader, so poll the USB IRQ flags
CFLAGS += -DUSE_USB_POLLING

# Number of bytes to reserve for spm_interface vector table (need 2 bytes for
# each entry to use `rjmp`)
SPM_INTERFACE_TABLE_SIZE = 48

CFLAGS += $(INC_PATHS)

# List C source files here.
C_SRC += $(SRC_USB) \
	descriptors.c \
	boot_protocol.c \
	vendor_report.c \
	util.c \
	main.c \

# List Assembler source files here.
# NOTE: Use *.S for user written asm files. *.s is used for compiler generated
ASM_SRC = \
	sp_driver.S \
	spm_interface.S \
	main_pre_init.S \

# Optimization level, can be [0, 1, 2, 3, s].
OPT = s

# List any extra directories to look for include files here.
EXTRAINCDIRS = $(XMEGA_PATH)/

# Compiler flag to set the C Standard level.
CSTANDARD = -std=gnu99

# Place -D or -U options here for C sources
CDEFS += -DF_CPU=$(F_CPU)UL
CDEFS += -DF_USB=$(F_USB)UL
CDEFS += -DBOARD=BOARD_$(BOARD)
CDEFS += -DARCH=ARCH_$(ARCH)
CDEFS += -D __$(DEVICE)__
CDEFS += $(USB_OPTS)

# Place -D or -U options here for ASM sources
ADEFS  = -DF_CPU=$(F_CPU)
ADEFS += -DF_USB=$(F_USB)UL
ADEFS += $(USB_OPTS)
ADEFS += -DBOARD=BOARD_$(BOARD)
ADEFS += -DARCH=ARCH_$(ARCH)
ADEFS += -D __$(DEVICE)__

# see avr-gcc for information on avrxmega2, avrxmega4, etc
# NOTE: haven't tested on all these chips
ifeq ($(MCU), atxmega16a4u)
  BOOT_SECTION_START = 0x004000
  BOOTLOADER_SIZE = 0x1000
  AVRDUDE_PART = x16a4
  LD_SCRIPT = avrxmega2.xn
  MCU_STRING = "ATxmega16a4u"
else ifeq ($(MCU), atxmega32a4u)
  BOOT_SECTION_START = 0x008000
  BOOTLOADER_SIZE = 0x1000
  AVRDUDE_PART = x32a4
  LD_SCRIPT = avrxmega2.xn
  MCU_STRING = "ATxmega32a4u"
else ifeq ($(MCU), atxmega64a4u)
  BOOT_SECTION_START = 0x010000
  BOOTLOADER_SIZE = 0x1000
  AVRDUDE_PART = x64a4
  LD_SCRIPT = avrxmega4.xn
  MCU_STRING = "ATxmega64a4u"
else ifeq ($(MCU), atxmega128a4u)
  BOOT_SECTION_START = 0x020000
  BOOTLOADER_SIZE = 0x2000
  AVRDUDE_PART = x128a4
  MCU_STRING = "ATxmega128a4u"
  # NOTE: avr-gcc says atxmega128a4u -> avrxmega7, but it also says avrxmega7
  # is for devices with more than 128KiB program memory and more than 64KiB
  # of RAM. So avrxmega7 is probably used with external RAM
  # LD_SCRIPT = avrxmega7.xn
  LD_SCRIPT = avrxmega6.xn
else
  $(error No part matches MCU='$(MCU)')
endif

CDEFS += -DMCU_STRING=\"$(MCU_STRING)\"

# LD_SCRIPT_DIR = /usr/lib/ldscripts
LD_SCRIPT_DIR = ./ld-scripts

LDFLAGS += -T $(LD_SCRIPT_DIR)/$(LD_SCRIPT)

LDFLAGS += -Wl,--section-start=.text=$(BOOT_SECTION_START)
LDFLAGS += -Wl,--section-start=.noinit=0x802400 # magic flag for bootloader entry
LDFLAGS += -Wl,--section-start=.spm_interface_table=$(shell python -c "print(hex($(BOOT_SECTION_START)+$(BOOTLOADER_SIZE)-$(SPM_INTERFACE_TABLE_SIZE)))")

all: hex fuse

# program a board using an external programmer
program: $(TARGET).hex
	$(AVRDUDE_CMD) -U flash:w:$<:i -E noreset

erase:
	$(AVRDUDE_CMD) -e

program-fuses:
	$(AVRDUDE_CMD) -U fuse0:w:"0x$(FUSE0)":m
	$(AVRDUDE_CMD) -U fuse1:w:"0x$(FUSE1)":m
	$(AVRDUDE_CMD) -U fuse2:w:"0x$(FUSE2)":m
	$(AVRDUDE_CMD) -U fuse4:w:"0x$(FUSE4)":m
	$(AVRDUDE_CMD) -U fuse5:w:"0x$(FUSE5)":m

include avr.mk

# Listing of phony targets.
.PHONY : all begin finish end sizebefore sizeafter gccversion \
build elf hex eep lss sym coff extcoff doxygen clean program-fuses \

