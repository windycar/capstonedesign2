# buzzer.py
import RPi.GPIO as GPIO
import time

class BuzzerController:
    BUZZER_PIN = 16 # Example GPIO pin
    
    def __init__(self):
        """Initializes the Buzzer."""
        # We assume RPi.GPIO.setmode(GPIO.BCM) is called ONCE in motor.py
        GPIO.setup(self.BUZZER_PIN, GPIO.OUT)
        GPIO.output(self.BUZZER_PIN, GPIO.LOW)
        self.is_buzzing = False
        print(f"BuzzerController initialized (using RPi.GPIO pin {self.BUZZER_PIN}).")

    def buzz_on(self):
        """Turns the buzzer on continuously (for Gas)."""
        if not self.is_buzzing:
            GPIO.output(self.BUZZER_PIN, GPIO.HIGH)
            self.is_buzzing = True

    def buzz_off(self):
        """Turns the buzzer off."""
        if self.is_buzzing:
            GPIO.output(self.BUZZER_PIN, GPIO.LOW)
            self.is_buzzing = False
    
    def beep_biyong(self):
        """Makes a 'Biyong Biyong' sound (for Pump)."""
        # This simulates 'Biyong' by two short beeps
        # This is a blocking call, but it's fast
        GPIO.output(self.BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.05) # Biyong
        GPIO.output(self.BUZZER_PIN, GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(self.BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.05) # Biyong
        GPIO.output(self.BUZZER_PIN, GPIO.LOW)
        self.is_buzzing = False

    def cleanup(self):
        """Stops the buzzer."""
        self.buzz_off()
        # GPIO.cleanup() will be called by motor_ctrl in main.py