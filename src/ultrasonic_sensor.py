import RPi.GPIO as gpio
import time
import threading



class UltrasonicSensor:	
    """ 
    Constructor Parameters:
	* trigger_pin - number for the GPIO pin connected to TRIG on the sensor
	* echo_pin - number for the GPIO pin connected to ECHO on the sensor
	* offset - distance from sensor when walker hits an obstacle
		^ can be zero
	* max_dist - ignores objects farther than this (after offset applied)
    """
    def __init__(self, trigger_pin, echo_pin, offset, max_dist, min_blip_freq, max_blip_freq):
        self.echo = echo_pin
        self.trigger = trigger_pin
        self.distance = 0
        self.dist_offset = offset
        self.dist_max = max_dist
        self.max_freq = max_blip_freq
        self.min_freq = min_blip_freq
        self.timeout = 0.05 #meters_to_seconds(10.0)
        gpio.setmode(gpio.BCM)
        gpio.setup(self.trigger, gpio.OUT)
        gpio.setup(self.echo, gpio.IN)

    def check_echo_started(self):
        return gpio.input(self.echo)

    def check_echo_ended(self):
        return not gpio.input(self.echo)

    def find_distance(self):
        time_check(self.check_echo_started, self.timeout)
        tmp_time = time_check(self.check_echo_ended, self.timeout)
        self.distance = seconds_to_meters( tmp_time ) - self.dist_offset
        print('sensor time', tmp_time)
        print('raw distance', self.distance)
        if self.distance < 0.0 or self.distance > self.dist_max:
            self.distance = 0.0
        #print('after correction', self.distance)

    def get_distance_thread(self):
        return threading.Thread(target=UltrasonicSensor.find_distance, args=(self,))

    def blips_freq(self):
        if self.distance > 0.0:
            return self.max_freq - (self.max_freq - self.min_freq) / self.dist_max * self.distance
        else:
            return 0.001



# def micros_to_cm(micros):
    # return micros / 58.82
def seconds_to_meters(seconds):
	return seconds * 170.145
def meters_to_seconds(meters):
	return meters / 170.145

def micros_wait(t):
    tEnd = time.time() + t * 10**-6
    while time.time() < tEnd:
        pass
    return

def time_check( return_checker, max_time ):
    tStart = time.time()
    tTimeout = tStart + max_time
    complete = return_checker()
    while not complete:
        complete = return_checker()
        if time.time() >= tTimeout: 
            return 0.0
    #print('sensor time', time.time() - tStart)
    return time.time() - tStart
    
