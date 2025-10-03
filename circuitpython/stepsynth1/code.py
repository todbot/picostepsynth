# stepsynth1.py -- basic step synth on PICOSTEPKNOBS hardware
import time
import random
import rainbowio
import synthio

import vectorio, displayio  # for display stuff

from picostepknobs import PicoStepKnobs

psk = PicoStepKnobs()

amp_env = synthio.Envelope(attack_time=0.1, decay_time = 0.05, release_time=0.3)

waveform_for_note = [ psk.waveforms[0], psk.waveforms[1], psk.waveforms[3], psk.waveforms[2] ]

print("hello from stepsynth1.py")
time.sleep(0.2)

base_note = 46

psk.leds.fill(0)
psk.leds.show()


def map_range(s, a1, a2, b1, b2): return  b1 + ((s - a1) * (b2 - b1) / (a2 - a1))

def play():
    play_pos = 0
    play_last_time = time.monotonic() - step_time

def stop():
    for i in range(8):
        if steps[i].note:
            psk.synth.release(steps[i].note)

def make_note(midi_note, waveid):
    plfo = synthio.LFO( rate=0.01, scale=0.001, offset=random.random()/100 )
    note = synthio.Note( frequency=synthio.midi_to_hz(midi_note),
                         envelope=amp_env,
                         bend=plfo,
                         waveform=psk.waveforms[ waveid ] )
    return note

# this display stuff will all go in a class soon

note_group = displayio.Group()
wave_group = displayio.Group()
nx,ny,nw,nh = 10,30,3,5
wx,wy,ww,wh = 10,60,3,5
dw,dh = psk.display.width, psk.display.height

def make_display():
    step_pal = displayio.Palette(2)
    step_pal[0] = 0xffffff  # the only color we got
    #step_pal[1] = 0x808080
    reticules = displayio.Group()
    reticules.append( vectorio.Rectangle(pixel_shader=step_pal, width=dw, height=1, x=0, y=dh//2) )
    psk.disp_group.append(reticules)

    for i in range(8):
        note_group.append(vectorio.Rectangle(pixel_shader=step_pal, width=nw, height=nh, x=nx+i*10, y=ny))
        wave_group.append(vectorio.Rectangle(pixel_shader=step_pal, width=ww, height=wh, x=wx+i*10, y=wy))
    psk.disp_group.append(note_group)
    psk.disp_group.append(wave_group)

def update_display(steps):
    for i in range(8):
        note_group[i].y = ny - steps[i].notenum // 5
        wave_group[i].y = wy - steps[i].waveid * 4
        #if i==0: print( note_group[i].height )

class Step:
    def __init__(self, notenum=0, waveid=0, enabled=False):
        self.notenum = notenum
        self.waveid = waveid
        self.enabled = enabled
        self.note = None
    def __repr__(self):
        return "step:"+str(self.notenum)+","+str(self.waveid)+","+str(self.enabled)

make_display()

steps = [Step(enabled=True, notenum=random.randint(33,65)) for i in range(8)]

update_display(steps)

print(steps)

playing = False
play_pos = 0
play_last_time = 0
step_time = 0.2
led_blink_time = 0
dim_by = 8
waveid_key_held = False

keys_held = [False] * 8
potvals = psk.read_all_pots()
knob_pickup = [False] * 8
knob_delta = [0] * 8  # used to show LEDs
# knob pickup logic
# - if
#

while True:
    # LED updating
    psk.leds.fill(0)
    for i in range(8):
        if playing:
            psk.leds[i] = 0xff00ff if steps[i].enabled else 0
            if i == play_pos:
                psk.leds[i] = 0xffffff  # highlight where playhead is
        else:
            psk.leds[i] = 0xff00ff if steps[i].note else 0
    # top 4 leds rotate through colors
    psk.leds[8+int((time.monotonic()*2) % 4)] = rainbowio.colorwheel( time.monotonic()*150 )
    psk.leds.show()     # show all the LED changes

    # KEY handling
    key = psk.keys.events.get()
    if key:
        print(key)
        n = key.key_number

        if n < 8:  # first 8 keys are note keys
            if key.pressed:
                print("pressed:", key.key_number)
                keys_held[n] = True
                if playing:
                    steps[n].enabled = not steps[n].enabled
                else:
                    note = make_note( steps[n].notenum, steps[n].waveid )
                    print(steps[n].notenum)
                    psk.synth.press( note )
                    steps[n].note = note
            if key.released:
                print("released:", key.key_number)
                keys_held[n] = True
                if not playing:
                    #if steps[n].note:
                    psk.synth.release( steps[n].note )
                    steps[n].note = None
                    print(steps)

        elif n == 8:  # play/stop key
            if key.pressed:
                playing = not playing
                if playing:
                    play()
                else:
                    stop()
                    print(steps)

        elif n == 9:  # waveid change key
            waveid_key_held = key.pressed
            print(steps)
            # reset knob pickup whether waveid key is pressed or released
            for i in range(8):
                knob_pickup[i] = False
            print(knob_pickup)

        elif n ==10:  # what does this key do?
            if key.pressed:
                #pot_print = not pot_print
                pass

    # KNOB handling
    potvals = psk.read_all_pots()

    # udpate step params on knob turns
    for i in range(8):
        if waveid_key_held:
            waveid = int(map_range(potvals[i], 0,255, 0,len(psk.waveforms)-1))

            if knob_pickup[i]:
                print("PICKUP!",i)
                steps[i].waveid = waveid

                if steps[i].note:
                    steps[i].note.waveform = psk.waveforms[ waveid ]

            if waveid == steps[i].waveid:
                knob_pickup[i] = True

        else:
            notenum = 20 + int(potvals[i] / 3)

            if knob_pickup[i]:
                steps[i].notenum = notenum

                if steps[i].note:
                    steps[i].note.frequency = synthio.midi_to_hz( steps[i].notenum )

            if notenum == steps[i].notenum:
                knob_pickup[i] = True


    # SEQUENCER
    if time.monotonic() - play_last_time >= step_time:
        play_last_time = time.monotonic()
        update_display(steps)
        if playing:
            last_note = steps[play_pos].note
            if last_note:
                psk.synth.release( last_note )
            play_pos = (play_pos + 1) % 8  # FIXME, allow more or fewer steps
            note = make_note( steps[play_pos].notenum, steps[play_pos].waveid )
            steps[play_pos].note = note
            if steps[play_pos].enabled:
                psk.synth.press( note )
        #if pot_print:
        #    print(' '.join(["%1X" % (int(v)>>12) for v in potvals]))
            #print(' '.join(["%03X" % int(v) for v in vals]))


    if time.monotonic() - led_blink_time > step_time * 8:
        led_blink_time = time.monotonic()
        psk.led.value = not psk.led.value
        #print("hi %.2f" % (time.monotonic() - st))


# 40 seconds after, it goes silent
