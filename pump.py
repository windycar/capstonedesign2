# pump.py
import RPi.GPIO as GPIO
import time

class PumpController:
    # Pin definitions (BCM) for L298N
    PUMP_IN1 = 5
    PUMP_IN2 = 6

    def __init__(self):
        """Initialize pump controller using RPi.GPIO"""
        # We assume RPi.GPIO.setmode(GPIO.BCM) is called ONCE in motor.py
        
        GPIO.setup(self.PUMP_IN1, GPIO.OUT)
        GPIO.setup(self.PUMP_IN2, GPIO.OUT)
        
        # Start with pump off
        GPIO.output(self.PUMP_IN1, GPIO.LOW)
        GPIO.output(self.PUMP_IN2, GPIO.LOW)
        
        print(f"PumpController initialized (using RPi.GPIO pins {self.PUMP_IN1}, {self.PUMP_IN2}).")

    def pump_on(self):
        """Turn the pump on (e.g., Forward)."""
        GPIO.output(self.PUMP_IN1, GPIO.HIGH)
        GPIO.output(self.PUMP_IN2, GPIO.LOW)

    def pump_off(self):
        """Turn the pump off (Stop/Brake)."""
        GPIO.output(self.PUMP_IN1, GPIO.LOW)
        GPIO.output(self.PUMP_IN2, GPIO.LOW)

    def cleanup(self):
        """Stops the pump."""
        print("Cleaning up Pump (RPi.GPIO)...")
        self.pump_off()
        # GPIO.cleanup() will be called by motor_ctrl in main.py