#!/usr/bin/env python3
"""
Example for using the RFM9x Radio with Raspberry Pi and LoRaWAN

Learn Guide: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
Author: Brent Rubell for Adafruit Industries
"""
import os
import threading
import time
import subprocess
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
# Import thte SSD1306 module.
import adafruit_ssd1306
# Import Adafruit TinyLoRa
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa

# Button A
btnA = DigitalInOut(board.D5)
btnA.direction = Direction.INPUT
btnA.pull = Pull.UP

# Button B
btnB = DigitalInOut(board.D6)
btnB.direction = Direction.INPUT
btnB.pull = Pull.UP

# Button C
btnC = DigitalInOut(board.D12)
btnC.direction = Direction.INPUT
btnC.pull = Pull.UP

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# 128x32 OLED Display
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3c)
# Clear the display.
display.fill(0)
display.show()
width = display.width
height = display.height

# TinyLoRa Configuration
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = DigitalInOut(board.CE0)
irq = DigitalInOut(board.D25)
# TTN Device Address, 4 Bytes, MSB
devaddr = bytearray([0x26, 0x01, 0x16, 0xF1])
# TTN Network Key, 16 Bytes, MSB
nwkey = bytearray([0x09, 0x2F, 0x27, 0x75, 0x33, 0xAD, 0x76, 0x3B,
                   0x5B, 0x6C, 0xE3, 0x3C, 0x9F, 0xB9, 0x7E, 0x9B])
# TTN Application Key, 16 Bytess, MSB
app = bytearray([0x41, 0x2A, 0xAA, 0x56, 0xE9, 0x27, 0x16, 0x70,
                 0x2B, 0x56, 0x8E, 0x2F, 0xBA, 0xE4, 0x66, 0x8F])
# Initialize ThingsNetwork configuration
ttn_config = TTN(devaddr, nwkey, app, country='EU')
# Initialize lora object
lora = TinyLoRa(spi, cs, irq, ttn_config)
# 2b array to store sensor data
data_pkt = bytearray(2)
# time to delay periodic packet sends (in seconds)
data_pkt_delay = 10.0

def send_pi_data_periodic():
    threading.Timer(data_pkt_delay, send_pi_data_periodic).start()
    print("Sending periodic data...")
    #Prepare the data
    #path = guess_battery_path()
    #print("Current battery percent: %d" % get_battery_percent(path))
    #print("Plugged in" if is_plugged(path) else "Not plugged in")
    

   # data = bytes("ba:3","utf-8")
    #data = 'ba:2,la:46.3234,lo:4.1234'
    #data = '107 58 51 44 99 58 51 48 48 44 101 58 49 50 51 52 44 97 58 50 54'.encode('utf-8')
    data = 'k:3'.encode('utf-8')
    print(data)
    print(data.hex()) # convert to hexadecimaé
   # send_pi_data(data.hex())

def send_pi_data(data):
    # Encode float as int
    #data.encode()
    data = int(data * 100)
    # Encode payload as bytes
    data_pkt[0] = (data >> 8) & 0xff
    data_pkt[1] = data & 0xff
    # Send data packet
    lora.send_data(data_pkt, len(data_pkt), lora.frame_counter)
    lora.frame_counter += 1
    display.fill(0)
    display.text('Sent Data to TTN!', 15, 15, 1)
    print('Data sent!')
    display.show()
    time.sleep(0.5)



BAT_PATH = "/proc/acpi/battery/BAT%d"
def is_plugged(batt_path):
    """Returns a flag saying if the battery is plugged in or not
    :param batt_path: The dir path to the battery (acpi) processes
    :type batt_path: string
    :returns: A flag, true is plugged, false unplugged
    :rtype: bool
    """
    p = subprocess.Popen(["grep","charging state",batt_path + "/state"],stdout=subprocess.PIPE)
    return "discharging" not in p.communicate()[0]


def get_full_charge(batt_path):
    """Get the max capacity of the battery
    :param batt_path: The dir path to the battery (acpi) processes
    :type batt_path: string
    :returns: The max capacity of the battery
    :rtype: int
     """
    p1 = subprocess.Popen(["grep","last full capacity",batt_path + "/info"],stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk","{print $4}"],stdin=p1.stdout,stdout=subprocess.PIPE)
    p1.stdout.close()
    return int(p2.communicate()[0])


def get_current_charge(batt_path):
    """Get the current capacity of the battery
    :param batt_path: The dir path to the battery (acpi) processes
    :type batt_path: string
    :returns: The current capacity of the battery
    :rtype: int
    """
    p1 = subprocess.Popen(["grep","remaining capacity",batt_path + "/state"],stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["awk","{print $3}"],stdin=p1.stdout,stdout=subprocess.PIPE)
    p1.stdout.close()
    return int(p2.communicate()[0])

def guess_battery_path():
    """Gets the path of the battery (BAT0, BAT1...)
    :returns: The path to the battery acpi process information
    :rtype: string
    """
    i = 0
    while True:
        if os.path.exists(BAT_PATH % i):
            return BAT_PATH % i
        i += 1

def get_battery_percent(batt_path):
    """Calculates the percent of the battery based on the different data of
    the battery processes
    :param batt_path: The dir path to the battery (acpi) processes
    :type batt_path: string
    :returns: The percent translation of the battery total and current capacity
    :rtype: int
    """
    return get_current_charge(batt_path) * 100 / get_full_charge(batt_path)


periodic = True

while True:
    packet = None
    # draw a box to clear the image
    display.fill(0)
    display.text('RasPi LoRaWAN', 35, 0, 1)
    display.show()
    # read the raspberry pi cpu load
    cmd = "top -bn1 | grep load | awk '{printf \"%.1f\", $(NF-2)}'"
    CPU = subprocess.check_output(cmd, shell = True )
    CPU = float(CPU)

    display.show()
    time.sleep(0.5)

    if periodic==True:
        send_pi_data_periodic()
        periodic=False


