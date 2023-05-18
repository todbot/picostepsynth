# hw_test1.py -- bring up PICOSTEPKNOBS hardware, playing audio while updating display
import time, random
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
import audiomixer, synthio
import ulab.numpy as np

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

SAMPLE_RATE = 28000  # clicks @ 36kHz & 48kHz on rp2040
SAMPLE_SIZE = 256    # we like powers of two
VOLUME = 12000       # 16384 is max volume I think

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

mixer = audiomixer.Mixer(voice_count=1, sample_rate=SAMPLE_RATE, channel_count=1,
                         bits_per_sample=16, samples_signed=True, buffer_size=8192 ) # buffer_size=4096 )
synth = synthio.Synthesizer(sample_rate=SAMPLE_RATE)  # note: no envelope or waveform, we do that in Note now!
audio.play(mixer)           # attach mixer to DAC
mixer.voice[0].play(synth)  # start synth engine playing

wave_saw = np.linspace(VOLUME, -VOLUME, num=SAMPLE_SIZE, dtype=np.int16)
wave_squ = np.concatenate((np.ones(SAMPLE_SIZE//2, dtype=np.int16)*VOLUME,np.ones(SAMPLE_SIZE//2, dtype=np.int16)*-VOLUME))
wave_sin = np.array(np.sin(np.linspace(0, 4*np.pi, SAMPLE_SIZE, endpoint=False)) * VOLUME, dtype=np.int16)
wave_noise = np.array([random.randint(-VOLUME, VOLUME) for i in range(SAMPLE_SIZE)], dtype=np.int16)
wave_sin_dirty = np.array( wave_sin + (wave_noise/4), dtype=np.int16)
waveform = np.zeros(SAMPLE_SIZE, dtype=np.int16)  # intially all zeros (silence)
waveforms = (wave_saw, wave_squ, wave_sin, wave_sin_dirty, wave_noise)
waveform[:] = waveforms[0]

amp_env = synthio.Envelope(attack_time=0.02, decay_time = 0.05, release_time=0.4,
                           attack_level=1, sustain_level=1.0)

notes_to_play = [43, 31, 64, 53]
note_i = 0

print("hello")
time.sleep(2)

dt = 0
import gc
while True:
    gc.collect()
    st = time.monotonic()
    #print("01234567890123456789")
    print("hi %3.3f" % dt) # time.monotonic())
    waveform[:] = waveforms[ random.randint(0,len(waveforms)-1) ]
    note = synthio.Note( frequency=synthio.midi_to_hz(notes_to_play[note_i]), envelope=amp_env, waveform=waveform )
    synth.release_all_then_press( (note,) )
    #note_i = (note_i + random.randint(0,2)) % len(notes_to_play)
    note_i = (note_i + 7) % len(notes_to_play)
    dt = time.monotonic() - st
    led.value = not led.value
    time.sleep(0.2 - dt)
    #time.sleep(1)
