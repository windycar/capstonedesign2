# servo.py
import RPi.GPIO as GPIO
import time

class ServoController:
    PAN_SERVO_PIN = 12
    TILT_SERVO_PIN = 19

    # --- Servo Angle Limits and Center ---
    MIN_PAN_ANGLE = 0
    MAX_PAN_ANGLE = 180
    CENTER_PAN_ANGLE = 90

    MIN_TILT_ANGLE = 0
    MAX_TILT_ANGLE = 180
    CENTER_TILT_ANGLE = 90 # Adjust based on your physical setup

    def __init__(self, frequency=50):
        # Assumes GPIO.setmode(GPIO.BCM) has been called in motor.py
        GPIO.setup(self.PAN_SERVO_PIN, GPIO.OUT)
        GPIO.setup(self.TILT_SERVO_PIN, GPIO.OUT)

        self.pan_pwm = GPIO.PWM(self.PAN_SERVO_PIN, frequency)
        self.tilt_pwm = GPIO.PWM(self.TILT_SERVO_PIN, frequency)

        self.pan_pwm.start(0)
        self.tilt_pwm.start(0)

        self.current_pan_angle = self.CENTER_PAN_ANGLE
        self.current_tilt_angle = self.CENTER_TILT_ANGLE
        
        # Set to initial center position
        self.set_angle(self.PAN_SERVO_PIN, self.CENTER_PAN_ANGLE)
        self.set_angle(self.TILT_SERVO_PIN, self.CENTER_TILT_ANGLE)

        print(f"ServoController initialized. Pan:{self.current_pan_angle}, Tilt:{self.current_tilt_angle}")

    def _angle_to_duty_cycle(self, angle):
        """Converts an angle (0-180) to a PWM duty cycle (2-12)."""
        # This mapping might need calibration for your specific servos
        return (angle / 18) + 2

    def set_angle(self, pin, angle):
        """Sets the angle of a specific servo."""
        if pin == self.PAN_SERVO_PIN:
            angle = _clamp_value(angle, self.MIN_PAN_ANGLE, self.MAX_PAN_ANGLE)
            self.current_pan_angle = angle
            self.pan_pwm.ChangeDutyCycle(self._angle_to_duty_cycle(angle))
        elif pin == self.TILT_SERVO_PIN:
            angle = _clamp_value(angle, self.MIN_TILT_ANGLE, self.MAX_TILT_ANGLE)
            self.current_tilt_angle = angle
            self.tilt_pwm.ChangeDutyCycle(self._angle_to_duty_cycle(angle))
        # time.sleep(0.02) # Give servo time to move (optional, depends on speed)

    def cleanup(self):
        """Stops PWM and cleans up GPIO."""
        self.pan_pwm.stop()
        self.tilt_pwm.stop()
        # GPIO.cleanup() will be called by motor_ctrl in main.py
        print("ServoController cleaned up.")

def _clamp_value(value, min_val, max_val):
    return max(min(value, max_val), min_val)