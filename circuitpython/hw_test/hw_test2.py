# hw_test2.py -- bring up PICOSTEPKNOBS hardware, just to see if we can
import time
import board
import busio
import audiobusio
import digitalio, analogio
import keypad
import neopixel, rainbowio
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1106

key_pins = (board.GP0, board.GP1, board.GP2, board.GP3, board.GP4,
            board.GP5, board.GP6, board.GP7, board.GP8, board.GP9, board.GP27)

potsel_pins = (board.GP10, board.GP11, board.GP12) # A,B,C

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

leds = neopixel.NeoPixel(neopixel_pin, 12, brightness=0.1, auto_write=False)
leds.fill(0xff00ff)

# Keys setup
keys = keypad.Keys(key_pins, value_when_pressed=False, pull=True)

# Pots setup
pot = analogio.AnalogIn(pot_pin)
pot_sels = []
for p in potsel_pins:
    ps = digitalio.DigitalInOut(p)
    ps.switch_to_output(value=False)
    pot_sels.append(ps)  # sure wish I could do this as a list comprehension

def read_pot(n):
    """Read pot n and return its value"""
    for i in range(3):
        pot_sels[i].value = n & (1<<i) != 0
    return pot.value

pot_vals = [0] * 8
def read_all_pots():
    for i in range(8):
        pot_vals[i] = read_pot(i)
    return pot_vals


print("hello")
time.sleep(0.5)

led_blink_time = 0
pot_disp_time = 0
while True:
    #leds[8:12] = [rainbowio.colorwheel( time.monotonic()*50)] * 4
    leds[8+int((time.monotonic()*2) % 4)] = rainbowio.colorwheel( time.monotonic()*150 )

    key = keys.events.get()
    if key:
        if key.pressed:
            print("pressed:", key.key_number)
            leds[key.key_number] = 0xffffff
        if key.released:
            leds[key.key_number] = 0
            print("released:", key.key_number)

    #print("01234567890123456789")
    vals = read_all_pots()
    for i in range(8):
        if leds[i] != (255,255,255):
            leds[i] = rainbowio.colorwheel(vals[i]>>8)
    leds.show()

    if time.monotonic() - pot_disp_time > 0.1:
        pot_disp_time = time.monotonic()
        print(' '.join(["%2X" % (v>>8) for v in vals]))

    if time.monotonic() - led_blink_time > 1.0:
        led_blink_time = time.monotonic()
        led.value = not led.value
        #print("hi %3.2f" % time.monotonic())
