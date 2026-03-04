#!/usr/bin/env python
import os
import usb.core
import usb.util
import sys

# Resolve firmware path relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FIRMWARE_PATH = os.path.join(SCRIPT_DIR, 'firmware_V2.bin')

# check for already initialized devices
initialized_v1 = list(usb.core.find(find_all=True, idVendor=0x05a9, idProduct=0x058a))
initialized_v2 = list(usb.core.find(find_all=True, idVendor=0x05a9, idProduct=0x058b))

if initialized_v1:
    print(f'Found {len(initialized_v1)} PS4 camera Version 1 already initialized')
if initialized_v2:
    print(f'Found {len(initialized_v2)} PS4 camera Version 2 already initialized')

# find all uninitialized devices
uninitialized_devices = list(usb.core.find(find_all=True, idVendor=0x05a9, idProduct=0x0580))
if not uninitialized_devices:
    print('No uninitialized PS4 cameras found')
    if not initialized_v1 and not initialized_v2:
        print('No PS4 cameras detected at all')
    sys.exit()

print(f'Found {len(uninitialized_devices)} uninitialized PS4 camera(s) to flash')

# helper function for chunking a file
def read_chunks(infile, chunk_size):
    while True:
        chunk = infile.read(chunk_size)
        if chunk:
            yield chunk
        else:
            return

def flash_device(dev, device_num):
    """Flash firmware to a single PS4 eye device"""
    try:
        print(f'Flashing device {device_num}...')
        
        # set the active configuration
        dev.set_configuration()
        
        chunk_size = 512
        index = 0x14
        value = 0
        
        # open firmware file for this device
        with open(FIRMWARE_PATH, "rb") as firmware:
            # transfer 512b chunks of the firmware
            for chunk in read_chunks(firmware, chunk_size):
                ret = dev.ctrl_transfer(0x40, 0x0, value, index, chunk)
                value += chunk_size
                if value >= 65536:
                    value = 0
                    index += 1
                if len(chunk) != ret:
                    print(f"Device {device_num}: sent {ret}/{len(chunk)} bytes")
        
        # command reboots device with new firmware and product id
        try:
            ret = dev.ctrl_transfer(0x40, 0x0, 0x2200, 0x8018, [0x5b])
        except usb.core.USBError:
            print(f'Device {device_num}: PS4 camera firmware uploaded and device reset')
            return True
            
    except Exception as e:
        print(f'Device {device_num}: Failed to flash firmware - {str(e)}')
        return False
    
    return True

# Flash firmware to all uninitialized devices
successful_flashes = 0
failed_flashes = 0

for i, dev in enumerate(uninitialized_devices, 1):
    if flash_device(dev, i):
        successful_flashes += 1
    else:
        failed_flashes += 1

print(f'\nFlashing complete:')
print(f'  Successfully flashed: {successful_flashes} device(s)')
print(f'  Failed to flash: {failed_flashes} device(s)')

if failed_flashes > 0:
    sys.exit(1)
else:
    print('All devices flashed successfully!')
