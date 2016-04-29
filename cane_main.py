# IMPORTS
from src.ultrasonic_sensor import UltrasonicSensor
from src.sox_sound_player import SoxSoundThread
import time
import threading

# GLOBALS
TRIG_L = 18
TRIG_R = 23 #fix
ECHO_LS = 23
ECHO_LF = 22
ECHO_RF = 20 #fix
ECHO_RS = 21 #fix
OFFSET_SIDE = 0.0
OFFSET_FRONT = 0.25
MAX_DIST_SIDE = 2.0
MAX_DIST_FRONT = 3.5
SOUND_LS = 'sound/98left.wav'
SOUND_LF = 'sound/884left.wav'
SOUND_RF = 'sound/884right.wav'
SOUND_RS = 'sound/98right.wav'
BLIP_FREQ_MIN = 0.25
BLIP_FREQ_MAX = 5.0


#TODO fix pin locations
sensors = [
    UltrasonicSensor(TRIG_L, ECHO_LS, OFFSET_SIDE, MAX_DIST_SIDE, BLIP_FREQ_MIN, BLIP_FREQ_MAX),
    UltrasonicSensor(TRIG_L, ECHO_LF, OFFSET_FRONT, MAX_DIST_FRONT, BLIP_FREQ_MIN, BLIP_FREQ_MAX),
    #UltrasonicSensor(TRIG_R, ECHO_RF, OFFSET_FRONT, MAX_DIST_FRONT, BLIP_FREQ_MIN, BLIP_FREQ_MAX),
    #UltrasonicSensor(TRIG_R, ECHO_RS, OFFSET_SIDE, MAX_DIST_SIDE, BLIP_FREQ_MIN, BLIP_FREQ_MAX),
]

sound_repeaters = [
    SoxSoundThread(SOUND_LS),
    SoxSoundThread(SOUND_LF),
    #SoxSoundThread(SOUND_RF),
    #SoxSoundThread(SOUND_RS),
]

try:
    for sr in sound_repeaters:
        sr.set_frequency(0.0001)
        sr.start()

    while True:
        sense_threads = [s.get_distance_thread() for s in sensors]
        for th in sense_threads:
            th.start()
        for th in sense_threads:
            th.join()

        for i in range(len(sound_repeaters)):
            sound_repeaters[i].set_frequency( sensors[i].blips_freq() )
            print('sensor', i, 'distance', sensors[i].distance, 'frequency', sensors[i].blips_freq())
        
        print( 'threads active', threading.active_count() )
        time.sleep(0.01)
        

except KeyboardInterrupt:
    for th in sense_threads:
        th.join()
    for sr in sound_repeaters:
        sr.stop_robotting()

