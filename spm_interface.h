// Copyright 2017 jem@seethis.link
// Licensed under the MIT license (http://opensource.org/licenses/MIT)

#pragma once

#include <avr/io.h>
#include <stdint.h>

#define SPM_FN_TABLE_SIZE 48
// How to use the spm interface functions in C from the application section.
// Example for ATxmega32a4u

#define BYTE_TO_WORD_ADDR(x) ((x) / 2)
#define SPM_FN_TABLE_BYTE_ADDR (BOOT_SECTION_END - (SPM_FN_TABLE_SIZE - 1))
#define SPM_FN_TABLE_ADDR (BYTE_TO_WORD_ADDR(SPM_FN_TABLE_BYTE_ADDR))

// The word addresses of the functions
#define SPM_ERASE_ADDR                     (SPM_FN_TABLE_ADDR + 0)
#define SPM_WRITE_ADDR                     (SPM_FN_TABLE_ADDR + 1)
#define SP_READCALIBRATIONBYTE_ADDR        (SPM_FN_TABLE_ADDR + 2)
#define SP_READFUSEBYTE_ADDR               (SPM_FN_TABLE_ADDR + 3)
#define SP_WRITELOCKBITS_ADDR              (SPM_FN_TABLE_ADDR + 4)
#define SP_READLOCKBITS_ADDR               (SPM_FN_TABLE_ADDR + 5)
#define SP_READUSERSIGNATUREBYTE_ADDR      (SPM_FN_TABLE_ADDR + 6)
#define SP_ERASEUSERSIGNATUREROW_ADDR      (SPM_FN_TABLE_ADDR + 7)
#define SP_WRITEUSERSIGNATUREROW_ADDR      (SPM_FN_TABLE_ADDR + 8)
#define SP_ERASEAPPLICATIONPAGE_ADDR       (SPM_FN_TABLE_ADDR + 9)
#define SP_ERASEWRITEAPPLICATIONPAGE_ADDR  (SPM_FN_TABLE_ADDR + 10)
#define SP_WRITEAPPLICATIONPAGE_ADDR       (SPM_FN_TABLE_ADDR + 11)
#define SP_LOADFLASHWORD_ADDR              (SPM_FN_TABLE_ADDR + 12)
#define SP_LOADFLASHPAGE_ADDR              (SPM_FN_TABLE_ADDR + 13)
#define SP_READFLASHPAGE_ADDR              (SPM_FN_TABLE_ADDR + 14)
#define SP_ERASEFLASHBUFFER_ADDR           (SPM_FN_TABLE_ADDR + 15)
#define SP_APPLICATIONCRC_ADDR             (SPM_FN_TABLE_ADDR + 16)
#define SP_BOOTCRC_ADDR                    (SPM_FN_TABLE_ADDR + 17)
#define SP_LOCKSPM_ADDR                    (SPM_FN_TABLE_ADDR + 18)
#define SP_WAITFORSPM_ADDR                 (SPM_FN_TABLE_ADDR + 19)


// call from application section

// This function erases the given flash page. The byte address may point anywhere
// inside the flash page.
// Note: This function is equivalent to calling `SP_EraseApplicationPage()` and
// `SP_WaitForSPM()`
#define SPM_flash_erase_page       ((void (*)(uint32_t addr))(SPM_ERASE_ADDR))

// This writes a flash page to the given byte address.
#define SPM_flash_write_page       ((void (*)(uint8_t* data, uint32_t addr))(SPM_WRITE_ADDR))

// The following functions are the same as those found in the ATMEL
// self-programming driver. See `sp_driver_h` for more information.
#define SP_ReadCalibrationByte       ((uint8_t (*)(uint8_t index))SP_READCALIBRATIONBYTE_ADDR)
#define SP_ReadFuseByte              ((uint8_t (*)(uint8_t index))SP_READFUSEBYTE_ADDR)
#define SP_WriteLockBits             ((void (*)(uint8_t data))SP_WRITELOCKBITS_ADDR)
#define SP_ReadLockBits              ((uint8_t (*)(void))SP_READLOCKBITS_ADDR)
#define SP_ReadUserSignatureByte     ((uint8_t (*)(uint16_t index))SP_READUSERSIGNATUREBYTE_ADDR)
#define SP_EraseUserSignatureRow     ((void (*)(void))SP_ERASEUSERSIGNATUREROW_ADDR)
#define SP_WriteUserSignatureRow     ((void (*)(void))SP_WRITEUSERSIGNATUREROW_ADDR)
#define SP_EraseApplicationPage      ((void (*)(uint32_t addr))SP_ERASEAPPLICATIONPAGE_ADDR)
#define SP_EraseWriteApplicationPage ((void (*)(uint32_t addr))SP_ERASEWRITEAPPLICATIONPAGE_ADDR)
#define SP_WriteApplicationPage      ((void (*)(uint32_t addr))SP_WRITEAPPLICATIONPAGE_ADDR)
#define SP_LoadFlashWord             ((void (*)(uint16_t addr, uint16_t data))SP_LOADFLASHWORD_ADDR)
#define SP_LoadFlashPage             ((void (*)(const uint8_t* data))SP_LOADFLASHPAGE_ADDR)
#define SP_ReadFlashPage             ((void (*)(const uint8_t* data, uint32_t addr))SP_READFLASHPAGE_ADDR)
#define SP_EraseFlashBuffer          ((void (*)(void))SP_ERASEFLASHBUFFER_ADDR)
#define SP_ApplicationCRC            ((uint32_t (*)(void))SP_APPLICATIONCRC_ADDR)
#define SP_BootCRC                   ((uint32_t (*)(void))SP_BOOTCRC_ADDR)
#define SP_LockSPM                   ((void (*)(void))SP_LOCKSPM_ADDR)
#define SP_WaitForSPM                ((void (*)(void))SP_WAITFORSPM_ADDR)
