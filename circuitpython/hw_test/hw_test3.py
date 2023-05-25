# hw_test3.py -- bring up PICOSTEPKNOBS hardware, just to see if we can
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
import audiomixer, synthio
import ulab.numpy as np
import random

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


# Synth setup

SAMPLE_RATE = 28000  # clicks @ 36kHz & 48kHz on rp2040
SAMPLE_SIZE = 256    # we like powers of two
SAMPLE_VOLUME = 32000  # 32767 is max volume I think

mixer = audiomixer.Mixer(voice_count=1, sample_rate=SAMPLE_RATE, channel_count=1,
                         bits_per_sample=16, samples_signed=True, buffer_size=8192 ) # need buffer because display
synth = synthio.Synthesizer(sample_rate=SAMPLE_RATE)  # note: no envelope or waveform, we do that in Note now!
audio.play(mixer)           # attach mixer to DAC
mixer.voice[0].level = 0.25  # pretty loud s turn it down
mixer.voice[0].play(synth)  # start synth engine playing

# Waveform setup
wave_saw = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)
wave_squ = np.concatenate((np.ones(SAMPLE_SIZE//2, dtype=np.int16)*SAMPLE_VOLUME,np.ones(SAMPLE_SIZE//2, dtype=np.int16)*-SAMPLE_VOLUME))
wave_sin = np.array(np.sin(np.linspace(0, 4*np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME, dtype=np.int16)
wave_noise = np.array([random.randint(-SAMPLE_VOLUME, SAMPLE_VOLUME) for i in range(SAMPLE_SIZE)], dtype=np.int16)
wave_sin_dirty = np.array( wave_sin + (wave_noise/4), dtype=np.int16)
waveforms = (wave_saw, wave_squ, wave_sin, wave_sin_dirty, wave_noise)

amp_env = synthio.Envelope(attack_time=0.002, decay_time = 0.05, release_time=0.05)

notes_to_play = [46, 50, 41, 58]# , 55, 55]
waveform_for_note = [ wave_sin, wave_saw, wave_squ, wave_saw, wave_squ, wave_squ]

print("hello")
time.sleep(0.5)

note_i = 1
offset = 1

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
        note_i = (note_i+1) % len(notes_to_play)
        note = synthio.Note( frequency=synthio.midi_to_hz(notes_to_play[note_i]+offset),
                             envelope=amp_env, waveform=waveform_for_note[note_i] )
        synth.release_all_then_press( note )
