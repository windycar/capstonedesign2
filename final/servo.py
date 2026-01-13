# servo.py
import RPi.GPIO as GPIO
import time

class ServoController:
    # --- [PIN MAP] ---
    PAN_SERVO_PIN = 12
    TILT_SERVO_PIN = 19
    # -----------------
    
    PWM_FREQ = 50
    
    # Initial Angles (Front / Down)
    INITIAL_PAN_ANGLE = 90
    INITIAL_TILT_ANGLE = 30

    def __init__(self):
        # Note: GPIO.setmode is handled in main.py
        
        GPIO.setup(self.PAN_SERVO_PIN, GPIO.OUT)
        GPIO.setup(self.TILT_SERVO_PIN, GPIO.OUT)
        
        self.pan_pwm = GPIO.PWM(self.PAN_SERVO_PIN, self.PWM_FREQ)
        self.tilt_pwm = GPIO.PWM(self.TILT_SERVO_PIN, self.PWM_FREQ)
        
        self.pan_pwm.start(0) 
        self.tilt_pwm.start(0)
        
        self.current_pan_angle = self.INITIAL_PAN_ANGLE
        self.current_tilt_angle = self.INITIAL_TILT_ANGLE
        
        print(f"ServoController initialized (Pins {self.PAN_SERVO_PIN}, {self.TILT_SERVO_PIN}).")
        
        # --- Force Move to Initial Position ---
        print(">>> Moving servos to START position... <<<")
        
        pan_duty = self._angle_to_duty_cycle(self.INITIAL_PAN_ANGLE)
        tilt_duty = self._angle_to_duty_cycle(self.INITIAL_TILT_ANGLE)
        
        self.pan_pwm.ChangeDutyCycle(pan_duty)
        self.tilt_pwm.ChangeDutyCycle(tilt_duty)
        
        time.sleep(1.0) # Wait 1.0s for physical movement
        
        # Cut power to prevent jitter
        self.pan_pwm.ChangeDutyCycle(0)
        self.tilt_pwm.ChangeDutyCycle(0)
        print(">>> Servos aligned and ready. <<<")

    def _angle_to_duty_cycle(self, angle):
        """Convert angle to duty cycle"""
        angle = max(0, min(180, angle))
        return 2.5 + (angle / 18.0)

    def set_angle(self, servo_pin, angle):
        """
        Move servo with soft motion
        """
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
            time.sleep(0.03) # Short pulse for smoothness
            pwm_instance.ChangeDutyCycle(0)

    def cleanup(self):
        self.pan_pwm.stop()
        self.tilt_pwm.stop()
        print("ServoController Cleaned up.")
