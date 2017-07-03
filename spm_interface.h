// Copyright 2017 jem@seethis.link
// Licensed under the MIT license (http://opensource.org/licenses/MIT)

#pragma once

#include <stdint.h>

// Erase the application page at the given byte address. The address can point
// anywhere inside the page.
// SPM interface table offset 0
void erase_application_page(uint32_t address);

// This function is used to write a page to the given byte address. The address
// can point anywhere inside the page.
// SPM interface table offset 1
void write_application_page(uint8_t *data, uint32_t address);
