# servo.py
import RPi.GPIO as GPIO
import time
import numpy as np 

class ServoController:
    # --- [NEW PIN MAP] ---
    PAN_SERVO_PIN = 12
    TILT_SERVO_PIN = 19
    # ---------------------
    
    PWM_FREQ = 50 # 50 Hz
    
    INITIAL_PAN_ANGLE = 90
    INITIAL_TILT_ANGLE = 0 # Your request: Tilt starts at the bottom

    def __init__(self):
        """Initialize servo controller using RPi.GPIO"""
        # We assume RPi.GPIO.setmode(GPIO.BCM) is called ONCE in motor.py
        
        GPIO.setup(self.PAN_SERVO_PIN, GPIO.OUT)
        GPIO.setup(self.TILT_SERVO_PIN, GPIO.OUT)
        
        self.pan_pwm = GPIO.PWM(self.PAN_SERVO_PIN, self.PWM_FREQ)
        self.tilt_pwm = GPIO.PWM(self.TILT_SERVO_PIN, self.PWM_FREQ)
        
        self.pan_pwm.start(0) # Start with 0 duty cycle
        self.tilt_pwm.start(0)
        
        self.current_pan_angle = self.INITIAL_PAN_ANGLE
        self.current_tilt_angle = self.INITIAL_TILT_ANGLE
        
        print(f"ServoController initialized (using RPi.GPIO pins {self.PAN_SERVO_PIN}, {self.TILT_SERVO_PIN}).")
        
        self.set_angle(self.PAN_SERVO_PIN, self.INITIAL_PAN_ANGLE)
        self.set_angle(self.TILT_SERVO_PIN, self.INITIAL_TILT_ANGLE)
        print(f"Servos initialized: Pan to {self.INITIAL_PAN_ANGLE} deg, Tilt to {self.INITIAL_TILT_ANGLE} deg.")

    def _angle_to_duty_cycle(self, angle):
        """Converts angle (0-180) to duty cycle using YOUR formula."""
        angle = max(0, min(180, angle))
        duty_cycle = 2.5 + (angle / 18.0) # YOUR working formula
        return duty_cycle

    def set_angle(self, servo_pin, angle):
        """Sets the angle using the 'One-Shot Pulse' method with YOUR timing."""
        duty_cycle = self._angle_to_duty_cycle(angle)
        
        pwm_instance = None
        if servo_pin == self.PAN_SERVO_PIN:
            pwm_instance = self.pan_pwm
            self.current_pan_angle = angle
        elif servo_pin == self.TILT_SERVO_PIN:
            pwm_instance = self.tilt_pwm
            self.current_tilt_angle = angle
        
        if pwm_instance:
            pwm_instance.ChangeDutyCycle(duty_cycle)
            time.sleep(0.005) # YOUR working sleep duration
            pwm_instance.ChangeDutyCycle(0) # YOUR working disable pulse

    def cleanup(self):
        """Stops servo pulses."""
        print("Cleaning up Servos (RPi.GPIO)...")
        self.pan_pwm.stop()
        self.tilt_pwm.stop()
        # GPIO.cleanup() will be called by motor_ctrl in main.py