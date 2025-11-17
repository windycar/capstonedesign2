# rgb_led.py
import RPi.GPIO as GPIO
import time

class RGBLed:
    # Using your pin map (Gas/Fire sensor pins)
    RED_PIN = 14
    GREEN_PIN = 15
    BLUE_PIN = 4
    
    def __init__(self):
        """Initializes the RGB LED."""
        # We assume RPi.GPIO.setmode(GPIO.BCM) is called ONCE in motor.py
        GPIO.setup(self.RED_PIN, GPIO.OUT)
        GPIO.setup(self.GREEN_PIN, GPIO.OUT)
        GPIO.setup(self.BLUE_PIN, GPIO.OUT)
        
        self.pwm_r = GPIO.PWM(self.RED_PIN, 100) # 100 Hz
        self.pwm_g = GPIO.PWM(self.GREEN_PIN, 100)
        self.pwm_b = GPIO.PWM(self.BLUE_PIN, 100)
        
        self.pwm_r.start(0)
        self.pwm_g.start(0)
        self.pwm_b.start(0)
        
        self.siren_state = 0
        print(f"RGBLed initialized (using RPi.GPIO pins R:{self.RED_PIN}, G:{self.GREEN_PIN}, B:{self.BLUE_PIN}).")

    def set_color(self, r, g, b):
        """Set color. R, G, B are 0-100 duty cycle."""
        self.pwm_r.ChangeDutyCycle(r)
        self.pwm_g.ChangeDutyCycle(g)
        self.pwm_b.ChangeDutyCycle(b)

    def set_off(self):
        self.set_color(0, 0, 0)

    def set_manual_mode(self):
        """[Normal] Solid Blue for Manual Mode."""
        self.set_color(0, 0, 100) # Solid Blue

    def set_auto_mode(self):
        """[Normal] Solid Green for Auto Mode."""
        self.set_color(0, 100, 0) # Solid Green

    def set_siren_effect(self):
        """[Special] Flashing Red/Blue for Gas Alert."""
        # This function must be called repeatedly in the loop
        # We use a simple time-based blink
        current_time_ms = int(time.time() * 10) # 10 times per second
        if current_time_ms % 4 < 2:
            self.set_color(100, 0, 0) # Red
        else:
            self.set_color(0, 0, 100) # Blue

    def cleanup(self):
        """Stops the LED PWM."""
        self.pwm_r.stop()
        self.pwm_g.stop()
        self.pwm_b.stop()
        # GPIO.cleanup() will be called by motor_ctrl in main.py