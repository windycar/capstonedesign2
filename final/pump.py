# pump.py
import RPi.GPIO as GPIO
import time

class PumpController:
    # --- [NEW] Pin definitions (BCM) for TB6612FNG ---
    # We assume a dedicated TB6612FNG driver for the pump
    # We re-use the pins you allocated for the L298N
    PUMP_IN1 = 5
    PUMP_IN2 = 6
    PUMP_PWM = 20  # This was ENA, now it's the PWM pin
    
    # We need a STBY pin for the TB6612FNG
    # Let's use a new pin, e.g., GPIO 21
    PUMP_STBY = 21 
    # --------------------------------------------------
    
    PWM_FREQ = 100 # PWM Frequency (100Hz is fine)
    PUMP_SPEED = 100 # Default pump speed (0-100%)

    def __init__(self):
        """Initialize pump controller using RPi.GPIO for TB6612FNG"""
        # We assume RPi.GPIO.setmode(GPIO.BCM) is called ONCE in motor.py
        
        GPIO.setup(self.PUMP_IN1, GPIO.OUT)
        GPIO.setup(self.PUMP_IN2, GPIO.OUT)
        GPIO.setup(self.PUMP_PWM, GPIO.OUT) 
        GPIO.setup(self.PUMP_STBY, GPIO.OUT) # [NEW] Setup STBY pin
        
        # [NEW] Create PWM instance
        self.pwm = GPIO.PWM(self.PUMP_PWM, self.PWM_FREQ)
        self.pwm.start(0) # Start with 0% duty cycle
        
        # Enable the driver
        GPIO.output(self.PUMP_STBY, GPIO.HIGH)
        
        # Start with pump off
        GPIO.output(self.PUMP_IN1, GPIO.LOW)
        GPIO.output(self.PUMP_IN2, GPIO.LOW)
        
        print(f"PumpController initialized (using TB6612FNG pins {self.PUMP_IN1}, {self.PUMP_IN2}, PWM:{self.PUMP_PWM}).")

    def pump_on(self):
        """Turn the pump on (e.g., Forward) at the set speed."""
        GPIO.output(self.PUMP_IN1, GPIO.HIGH)
        GPIO.output(self.PUMP_IN2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(self.PUMP_SPEED) # Set PWM speed

    def pump_off(self):
        """Turn the pump off (Stop/Brake)."""
        GPIO.output(self.PUMP_IN1, GPIO.LOW) # Use LOW/LOW for coast (less stress)
        GPIO.output(self.PUMP_IN2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0) # Set PWM speed to 0

    def cleanup(self):
        """Stops the pump and PWM."""
        print("Cleaning up Pump (TB6612FNG)...")
        self.pump_off()
        self.pwm.stop() 
        GPIO.output(self.PUMP_STBY, GPIO.LOW) # Disable driver
        # GPIO.cleanup() will be called by motor_ctrl in main.py
