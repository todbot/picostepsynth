# hw_test3.py -- bring up PICOSTEPKNOBS hardware, just to see if we can
import time
# import board
# import busio
# import audiobusio
# import digitalio, analogio
# import keypad
# import neopixel
# import displayio
# import terminalio
# from adafruit_display_text import label
# import adafruit_displayio_sh1106
# import audiomixer, synthio
# import ulab.numpy as np
# import random

import rainbowio
import synthio
import picostepknobs

psk = picostepknobs.PicoStepKnobs()


amp_env = synthio.Envelope(attack_time=0.002, decay_time = 0.05, release_time=0.05)

notes_to_play = [46, 50, 41, 58]#, 55, 55]
waveform_for_note = [ psk.waveforms[0], psk.waveforms[1], psk.waveforms[3], psk.waveforms[2] ]

print("hello")
time.sleep(0.5)

note_i = 1
offset = 1

led_blink_time = 0
pot_disp_time = 0

base_note = 46
notes_pressed = {}

def note_on(n):
    note_i = base_note + n
    note = synthio.Note( frequency=synthio.midi_to_hz(note_i),
                         envelope=amp_env,
                         waveform=waveform_for_note[note_i%len(waveform_for_note)] )
    notes_pressed[n] = note
    psk.synth.press(note)

def note_off(n):
    note = notes_pressed.get(n,None)
    if note:
        psk.synth.release(note)
    else:
        print("BAD NOTE",n)

st = time.monotonic()

while True:
    #leds[8:12] = [rainbowio.colorwheel( time.monotonic()*50)] * 4
    psk.leds[8+int((time.monotonic()*2) % 4)] = rainbowio.colorwheel( time.monotonic()*150 )

    key = psk.keys.events.get()
    if key:
        if key.pressed:
            print("pressed:", key.key_number)
            psk.leds[key.key_number] = rainbowio.colorwheel( time.monotonic()*50 )
            note_on(key.key_number)
        if key.released:
            psk.leds[key.key_number] = 0
            print("released:", key.key_number)
            note_off(key.key_number)

    #print("01234567890123456789")
    vals = psk.read_all_pots()

    #psk.leds.show()

    if time.monotonic() - pot_disp_time > 0.1:
        pot_disp_time = time.monotonic()
        print(' '.join(["%02X" % (int(v)>>8) for v in vals]))
        #print(' '.join(["%03X" % int(v) for v in vals]))

    if time.monotonic() - led_blink_time > 1.0:
        led_blink_time = time.monotonic()
        psk.led.value = not psk.led.value
        print("hi %.2f" % (time.monotonic() - st))


# 40 seconds after, it goes silent
