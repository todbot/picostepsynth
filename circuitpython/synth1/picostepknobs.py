
import board
import busio
import audiobusio
import digitalio, analogio
import keypad
import neopixel
import displayio
import adafruit_displayio_sh1106
import audiomixer
import synthio
import ulab.numpy as np
import random

import time # for debugging

key_pins = (board.GP0, board.GP1, board.GP2, board.GP3, board.GP4,
            board.GP5, board.GP6, board.GP7, board.GP8, board.GP9, board.GP27)

potsel_pins = (board.GP10, board.GP11, board.GP12) # 4051 A,B,C

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

power_save_pin = board.GP23  # set HIGH to get better ripple for ADC

led_pin = board.GP25 # built-in LED on Pico
pot_pin = board.GP28

dw,dh = 132,64

SAMPLE_RATE = 22000  # clicks @ 36kHz & 48kHz on rp2040
SAMPLE_SIZE = 256    # we like powers of two
SAMPLE_VOLUME = 32000  # 32767 is max volume I think

class PicoStepKnobs():
    def __init__(self):
        # Audio output setup
        self.audio = audiobusio.I2SOut(bit_clock=i2s_bck_pin, word_select=i2s_lck_pin, data=i2s_dat_pin)
        # need big buffer because display
        self.mixer = audiomixer.Mixer(voice_count=1, sample_rate=SAMPLE_RATE, channel_count=1,
                                      bits_per_sample=16, samples_signed=True,
                                      buffer_size=4096 )
                                      #buffer_size=8192 )
        # Synth setup
        self.synth = synthio.Synthesizer(sample_rate=SAMPLE_RATE, channel_count=1)
        self.audio.play(self.mixer)           # attach mixer to DAC
        self.mixer.voice[0].level = 0.25  # pretty loud s turn it down
        self.mixer.voice[0].play(self.synth)  # start synth engine playing

        # Display setup
        displayio.release_displays()
        self.spi = busio.SPI(clock=disp_sclk, MOSI=disp_mosi)
        self.display_bus = displayio.FourWire(self.spi, command = disp_dc, chip_select = disp_cs, reset=disp_res)
        self.display = adafruit_displayio_sh1106.SH1106(self.display_bus, width=dw, height=dh, colstart=3)

        # MIDI setup
        self.midi_uart = busio.UART(tx=midi_tx_pin, rx=midi_rx_pin, baudrate=31250) # timeout=midi_timeout)

        # LED setup
        self.led = digitalio.DigitalInOut(led_pin)
        self.led.switch_to_output(value=True)
        self.power_save = digitalio.DigitalInOut(power_save_pin)
        self.power_save.switch_to_output(value = True)

        self.leds = neopixel.NeoPixel(neopixel_pin, 12, brightness=0.1, auto_write=False)
        self.leds.fill(0xff00ff)

        # Keys setup
        self.keys = keypad.Keys(key_pins, value_when_pressed=False, pull=True)

        # Pots setup
        self.pot = analogio.AnalogIn(pot_pin)
        self.pot_sels = []
        self.pot_vals = [0] * 8
        for p in potsel_pins:
            ps = digitalio.DigitalInOut(p)
            ps.switch_to_output(value=False)
            self.pot_sels.append(ps)  # sure wish I could do this as a list comprehension

        # Waveform setup
        wave_saw = np.linspace(SAMPLE_VOLUME, -SAMPLE_VOLUME, num=SAMPLE_SIZE, dtype=np.int16)
        wave_squ = np.concatenate((np.ones(SAMPLE_SIZE//2, dtype=np.int16)*SAMPLE_VOLUME,
                                   np.ones(SAMPLE_SIZE//2, dtype=np.int16)*-SAMPLE_VOLUME))
        wave_sin = np.array(np.sin(np.linspace(0, 4*np.pi, SAMPLE_SIZE, endpoint=False)) * SAMPLE_VOLUME,
                            dtype=np.int16)
        wave_noise = np.array([random.randint(-SAMPLE_VOLUME, SAMPLE_VOLUME) for i in range(SAMPLE_SIZE)],
                              dtype=np.int16)
        wave_sin_dirty = np.array( wave_sin + (wave_noise/4), dtype=np.int16)
        self.waveforms = (wave_saw, wave_squ, wave_sin, wave_sin_dirty, wave_noise)


    def read_pot(self,n):
        """Read pot n and return its value"""
        for b in range(3):
            self.pot_sels[b].value = n & (1<<b) != 0
        return self.pot.value

    def read_all_pots(self):
        filt = 0.75
        for i in range(8):
            self.pot_vals[i] = filt*self.pot_vals[i] + (1-filt)*self.read_pot(i) #filter
        return self.pot_vals
