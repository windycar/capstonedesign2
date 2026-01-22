# fire_sensor.py
import RPi.GPIO as GPIO

class FireSensor:
    # Pin Definition (BCM)
    PIN_FLAME = 24

    def __init__(self):
        GPIO.setup(self.PIN_FLAME, GPIO.IN)
        print(f"FireSensor: Initialized on Pin {self.PIN_FLAME}.")

    def is_fire_detected(self):
        """Returns True if fire is detected (Low signal)"""
        return GPIO.input(self.PIN_FLAME) == 0
