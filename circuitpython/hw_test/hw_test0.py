# hw_test0.py -- bring up PICOSTEPKNOBS hardware, just to see if we can
import time
import board
import busio
import audiobusio
import digitalio
import keypad
import neopixel
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1106

key_pins = (board.GP0, board.GP1, board.GP2, board.GP3, board.GP4,
            board.GP5, board.GP6, board.GP7, board.GP8, board.GP9, board.GP27)

potselA_pin = board.GP10
potselB_pin = board.GP11
potselC_pin = board.GP12

i2s_lck_pin = board.GP14
i2s_bck_pin = board.GP13
i2s_dat_pin = board.GP15

midi_tx_pin = board.GP16
midi_rx_pin = board.GP17

disp_sclk = board.GP18
disp_mosi = board.GP19
disp_dc   = board.GP20
disp_cs   = board.GP21
disp_res  = board.GP22  # or could use 10uF/10k RC circuit instead of GPIO

neopixel_pin = board.GP26
led_pin = board.GP25 # built-in LED on Pico
pot_pin = board.GP28


# Audio output setup
audio = audiobusio.I2SOut(bit_clock=i2s_bck_pin, word_select=i2s_lck_pin, data=i2s_dat_pin)

# Display setup
displayio.release_displays()
dw,dh = 132,64
spi = busio.SPI(clock=disp_sclk, MOSI=disp_mosi)
display_bus = displayio.FourWire(spi, command = disp_dc, chip_select = disp_cs, reset=disp_res)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=dw, height=dh, colstart=3)

# MIDI setup
midi_uart = busio.UART(tx=midi_tx_pin, rx=midi_rx_pin, baudrate=31250) # timeout=midi_timeout)

# LED setup
led = digitalio.DigitalInOut(led_pin)
led.switch_to_output(value=True)
#leds = neopixel.NeoPixel(neopixel_pin, 1, brightness=0.2)

# Keys setup
keys = keypad.Keys(key_pins, value_when_pressed=False, pull=True)


print("hello")
time.sleep(2)

while True:
    print("01234567890123456789")
    print("hi %3.2f" % time.monotonic())
    led.value = not led.value
    time.sleep(0.15)
