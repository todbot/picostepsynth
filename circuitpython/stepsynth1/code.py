# stepsynth1.py -- basic step synth on PICOSTEPKNOBS hardware
import time
import random
import rainbowio
import synthio
import picostepknobs

psk = picostepknobs.PicoStepKnobs()

amp_env = synthio.Envelope(attack_time=0.1, decay_time = 0.05, release_time=0.3)

waveform_for_note = [ psk.waveforms[0], psk.waveforms[1], psk.waveforms[3], psk.waveforms[2] ]

print("hello from stepsynth1.py")
time.sleep(0.2)

base_note = 46

psk.leds.fill(0)
psk.leds.show()

st = time.monotonic()

pot_print = False
playing = False
play_pos = 0
play_last_time = 0
play_time = 0.2
led_blink_time = 0
dim_by = 8

def map_range(s, a1, a2, b1, b2): return  b1 + ((s - a1) * (b2 - b1) / (a2 - a1))

def play():
    play_pos = 0
    play_last_time = time.monotonic() - play_time

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

class Step:
    def __init__(self, notenum=0, waveid=0, enabled=False):
        self.notenum = notenum
        self.waveid = waveid
        self.enabled = enabled
        self.note = None
    def __repr__(self):
        return "step:"+str(self.notenum)+","+str(self.waveid)+","+str(self.enabled)

steps = [Step(enabled=True) for i in range(8)]


waveid_key_held = False

while True:
    #psk.leds[:] = [[max(i-dim_by,0) for i in l] for l in psk.leds] # dim all by (dim_by,dim_by,dim_by)
    psk.leds.fill(0)

    for i in range(8):
        if playing:
            psk.leds[i] = 0xff00ff if steps[i].enabled else 0
            if i == play_pos:
                psk.leds[i] = 0xffffff  # highlight where playhead is
        else:
            pass

    # top leds rotate through colors
    psk.leds[8+int((time.monotonic()*2) % 4)] = rainbowio.colorwheel( time.monotonic()*150 )
    # show all the LED changes
    psk.leds.show()

    key = psk.keys.events.get()
    if key:
        print(key)
        n = key.key_number
        if n < 8:  # first 8 keys are note keys
            if key.pressed:
                print("pressed:", key.key_number)
                if playing:
                    steps[n].enabled = not steps[n].enabled
                else:
                    note = make_note( steps[n].notenum, steps[n].waveid )
                    print(steps[n].notenum)
                    psk.synth.press( note )
                    steps[n].note = note
            if key.released:
                if not playing:
                    print("released:", key.key_number)
                    #if steps[n].note:
                    psk.synth.release( steps[n].note )
                    steps[n].note = None
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

        elif n ==10:
            if key.pressed:
                pot_print = not pot_print


    #print("01234567890123456789")
    potvals = psk.read_all_pots()

    # fixme only do this when holding note key

    for i in range(8):
        if waveid_key_held:
            waveid = int(map_range(potvals[i], 0,65535, 0,len(psk.waveforms)))
            steps[i].waveid = waveid
            if steps[i].note and not playing:
                steps[i].note.waveform = psk.waveforms[ waveid ]
        else:
            steps[i].notenum = int(potvals[i] / 768)  # fractional midi notes!
            if steps[i].note and not playing:  # held while not playing
                steps[i].note.frequency = synthio.midi_to_hz( steps[i].notenum )


    if time.monotonic() - play_last_time > play_time:
        play_last_time = time.monotonic()
        if playing:
            last_note = steps[play_pos].note
            if last_note:
                psk.synth.release( last_note )
            play_pos = (play_pos + 1) % 8  # FIXME, allow more or fewer steps
            note = make_note( steps[play_pos].notenum, steps[play_pos].waveid )
            steps[play_pos].note = note
            if steps[play_pos].enabled:
                psk.synth.press( note )
        if pot_print:
            print(' '.join(["%1X" % (int(v)>>12) for v in potvals]))
            #print(' '.join(["%03X" % int(v) for v in vals]))


    if time.monotonic() - led_blink_time > 1.0:
        led_blink_time = time.monotonic()
        psk.led.value = not psk.led.value
        #print("hi %.2f" % (time.monotonic() - st))


# 40 seconds after, it goes silent
