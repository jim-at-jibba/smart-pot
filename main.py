
#!/usr/bin/env python

import json
import time
import colorsys
import os
import sys
import ST7735
try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

from bme280 import BME280
from enviroplus import gas
from subprocess import PIPE, Popen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""all-in-one.py - Displays readings from all of Enviro plus' sensors
Press Ctrl+C to exit!
""")

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# Create ST7735 LCD display class
st7735 = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
st7735.begin()

WIDTH = st7735.width
HEIGHT = st7735.height

# Set up canvas and font
img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
draw = ImageDraw.Draw(img)
path = os.path.dirname(os.path.realpath(__file__))
font = ImageFont.truetype(path + "/fonts/Asap/Asap-Bold.ttf", 25)

message = ""

size_x, size_y = draw.textsize(message, font)
text_colour = (255, 255, 255)
back_colour = (0, 170, 170)
warning_colour = (255, 0, 0)
# Calculate text position

# Displays data and text on the 0.96" LCD
def display_text(state):
    x = (WIDTH - size_x) / 2
    y = (HEIGHT / 2) - (size_y / 2)
    # Maintain length of list
    name_string = "Name: {}".format(name)
    draw.rectangle((0, 0, 160, 80), back_colour)
    draw.text((0,0), name_string, font=font, fill=(0,0,0))
    draw.text((0, 30), state, font=font, fill=(0, 0, 0))
    st7735.display(img)


def display_warning(variable, data, unit, state):
    x = (WIDTH - size_x) / 2
    y = (HEIGHT / 2) - (size_y / 2)
    # Maintain length of list
    message = "{}: {:.1f} {}".format(variable[:4], data, unit)
    logging.info(message)
    draw.rectangle((0, 0, 160, 80), warning_colour)
    draw.text((0, 0), message, font=font, fill=(255, 255, 255))
    draw.text((0, 30), state, font=font, fill=(255, 255, 255))
    st7735.display(img)

# Get the temperature of the CPU for compensation
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])


# Tuning factor for compensation. Decrease this number to adjust the
# temperature down, and increase to adjust up
factor = 0.8

cpu_temps = [get_cpu_temperature()] * 5

delay = 0.5  # Debounce the proximity tap
mode = 0  # The starting mode
last_page = 0
light = 1

# Plant Settings
maxTemp = 25
minTemp = 10
minLight = 150
maxLight = 300
name = ""

def read_json():
    global maxTemp
    global minTemp
    global minLight
    global maxLight
    global name
    logging.info("READING JSON")
    # Read JSON
    with open('settings.json', 'r') as settings:
        data=settings.read()
        obj = json.loads(data)

    minTemp=obj['settings']['temp']['min']
    maxTemp=obj['settings']['temp']['max']
    minLight=obj['settings']['lux']['min']
    maxLight=obj['settings']['lux']['max']
    name=str(obj['settings']['name'])
    logging.info("NEW VALUES, temp: {} {}, light: {} {}".format(minTemp, maxTemp, minLight, maxLight))

# Read JSON
with open('settings.json', 'r') as settings:
    data=settings.read()
    obj = json.loads(data)

# The main loop
try:
    while True:
        read_json()

        # Prox
        proximity = ltr559.get_proximity()

        # Temp
        cpu_temp = get_cpu_temperature()
        # Smooth out with some averaging to decrease jitter
        cpu_temps = cpu_temps[1:] + [cpu_temp]
        avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
        raw_temp = bme280.get_temperature()
        temp = raw_temp - ((avg_cpu_temp - raw_temp))

        # humidity
        humidity = bme280.get_humidity()

        # Lux
        lux = ltr559.get_lux()

        logging.info("TEMP: {} RAW: {:.1f} LUX: {}".format(temp, raw_temp, lux))

        if temp <= minTemp:
            unit = "C"
            data = temp
            display_warning("Temp", data, unit, "To cold")
        elif temp > maxTemp:
            unit = "C"
            data = temp
            display_warning("Temp", data, unit, "To hot")
        elif lux < minLight:
            unit = "Lux"
            data = lux
            display_warning("Light", data, unit, "To dark")
        elif lux > maxLight:
            unit = "Lux"
            data = lux
            display_warning("Light", data, unit, "To light")
        else:
            display_text("Happy Plant")

        time.sleep(2)
# Exit cleanly
except KeyboardInterrupt:
    sys.exit(0)
