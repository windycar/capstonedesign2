# rgb_led.py
import RPi.GPIO as GPIO
import time

class RGBController:
    # Pin Definitions (BCM)
    PIN_R = 14
    PIN_G = 15
    PIN_B = 4

    def __init__(self):
        GPIO.setup(self.PIN_R, GPIO.OUT)
        GPIO.setup(self.PIN_G, GPIO.OUT)
        GPIO.setup(self.PIN_B, GPIO.OUT)
        
        self.last_blink_time = 0
        self.blink_state = False
        
        self.turn_off()
        print("RGBController Initialized (R:14, G:15, B:4).")

    def set_color(self, r, g, b):
        """Set RGB color directly (1=ON, 0=OFF)"""
        GPIO.output(self.PIN_R, GPIO.HIGH if r else GPIO.LOW)
        GPIO.output(self.PIN_G, GPIO.HIGH if g else GPIO.LOW)
        GPIO.output(self.PIN_B, GPIO.HIGH if b else GPIO.LOW)

    def set_manual_mode(self):
        """Blue for Manual Mode (Idle)"""
        self.set_color(0, 0, 1)

    def set_auto_mode(self):
        """Green for Auto Mode (Idle)"""
        self.set_color(0, 1, 0)

    def turn_off(self):
        """Turn off all LEDs"""
        self.set_color(0, 0, 0)

    def blink_red_effect(self):
        """
        Non-blocking Red Blink Effect (Fire Truck Style).
        Must be called continuously in the loop.
        """
        current_time = time.time()
        # Blink every 0.1 seconds
        if current_time - self.last_blink_time > 0.1:
            self.blink_state = not self.blink_state
            self.last_blink_time = current_time
        
        if self.blink_state:
            self.set_color(1, 0, 0) # Red ON
        else:
            self.set_color(0, 0, 0) # Red OFF

    def cleanup(self):
        self.turn_off()
        print("RGBController Cleaned up.")