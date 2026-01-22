# buzzer.py
import RPi.GPIO as GPIO

class BuzzerController:
    # Pin Definition (BCM)
    PIN_BUZZER = 16

    def __init__(self):
        GPIO.setup(self.PIN_BUZZER, GPIO.OUT)
        

        self.pwm = GPIO.PWM(self.PIN_BUZZER, 1500) 
        self.pwm.start(0) 
        
        print(f"BuzzerController Initialized (Pin {self.PIN_BUZZER}, Freq: 2kHz).")

    def on(self):
        """Turn buzzer ON (50% Duty Cycle)"""
        self.pwm.ChangeDutyCycle(50) 

    def off(self):
        """Turn buzzer OFF (0% Duty Cycle)"""
        self.pwm.ChangeDutyCycle(0)

    def cleanup(self):
        self.pwm.stop()
        print("BuzzerController Cleaned up.")
