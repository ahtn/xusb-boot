; Copyright 2017 jem@seethis.link
; Licensed under the MIT license (http://opensource.org/licenses/MIT)

#include <avr/io.h>

#define NVM_CMD_NO_OPERATION_gc (0x00<<0)   // Noop/Ordinary LPM

; avr-asm notes
; caller saved registers
; r18-r27, Z(r30-r31)
.section .text

.global erase_application_page_fn
; ---
; This routine erases the page at address R25:R24:R23:R22 in the application
; section. The address can point anywhere inside the page.
; Input:
;     R25:R24:R23:R22 - Byte address into Flash page.
;
; Returns:
;     Nothing.
; ---
erase_application_page_fn:
	rcall	SP_EraseApplicationPage
	rcall	SP_WaitForSPM
	ldi	r18, NVM_CMD_NO_OPERATION_gc
	sts	NVM_CMD, r18
	ret

.global write_application_page_fn
; ---
; 1. This routine flushes the Flash page buffer.
;
; 2. This routine writes an entire page from the SRAM buffer at
; address R25:R24 into the Flash page buffer.
;
; 3. This routine writes the page buffer to the Flash page at address R23:R22:R21:R20
; in the application section. The address can point anywhere inside the page.
;
; Input:
;     R25:R24 - 16-bit pointer to SRAM buffer.
;     R23:R22:R21:R20 - Byte address into Flash page.
;
; Returns:
;     Nothing.
; ---
write_application_page_fn:
	; save flash address (r23-r20) to stack
	push	r23
	push	r22
	push	r21
	push	r20
	rcall	SP_EraseFlashBuffer	; flush flash page buffer
	rcall	SP_WaitForSPM

	rcall	SP_LoadFlashPage	; load the flash page buffer (R25:R24)
	rcall	SP_WaitForSPM

	pop	r22			; restore flash address to R25:R24:R23:R22
	pop	r23
	pop	r24
	pop	r25
	rcall	SP_WriteApplicationPage	; write the flash page buffer
	rcall	SP_WaitForSPM

	ldi	r18, NVM_CMD_NO_OPERATION_gc
	sts	NVM_CMD, r18

	ret


.section .spm_interface_table,"ax",@progbits

.global erase_application_page
erase_application_page:
	jmp	erase_application_page_fn

.global write_application_page
write_application_page:
	jmp	write_application_page_fn
