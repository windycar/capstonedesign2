# motor.py
import RPi.GPIO as GPIO

class MotorController:
    # Pin definitions (BCM) for TB6612FNG
    STBY = 17
    AIN1 = 27
    AIN2_PIN = 18
    PWMA = 22

    BIN1 = 13
    BIN2_PIN = 23
    PWMB = 26

    def __init__(self, pwm_freq=1000):
        """Initialize motor controller and setup GPIO pins"""
        # Using RPi.GPIO for motors as pigpio is for servos
        GPIO.setmode(GPIO.BCM)
        
        GPIO.setup(self.STBY, GPIO.OUT)
        
        # Setup Motor A (Left) pins
        GPIO.setup(self.AIN1, GPIO.OUT)
        GPIO.setup(self.AIN2_PIN, GPIO.OUT)
        GPIO.setup(self.PWMA, GPIO.OUT)
        
        # Setup Motor B (Right) pins
        GPIO.setup(self.BIN1, GPIO.OUT)
        GPIO.setup(self.BIN2_PIN, GPIO.OUT)
        GPIO.setup(self.PWMB, GPIO.OUT)
        
        self.p_a = GPIO.PWM(self.PWMA, pwm_freq)
        self.p_b = GPIO.PWM(self.PWMB, pwm_freq)
        
        self.p_a.start(0)
        self.p_b.start(0)
        
        GPIO.output(self.STBY, GPIO.HIGH)
        print("MotorController initialized (using RPi.GPIO).")

    def set_left_motor(self, speed):
        """
        Controls the speed and direction of the left motor (A).
        speed: -100 (Reverse) to 100 (Forward)
        """
        speed = max(min(speed, 100), -100) 

        if speed > 0:
            GPIO.output(self.AIN1, GPIO.HIGH)
            GPIO.output(self.AIN2_PIN, GPIO.LOW)
            self.p_a.ChangeDutyCycle(speed)
        elif speed < 0:
            GPIO.output(self.AIN1, GPIO.LOW)
            GPIO.output(self.AIN2_PIN, GPIO.HIGH)
            self.p_a.ChangeDutyCycle(abs(speed))
        else:
            GPIO.output(self.AIN1, GPIO.HIGH)
            GPIO.output(self.AIN2_PIN, GPIO.HIGH)
            self.p_a.ChangeDutyCycle(0)

    def set_right_motor(self, speed):
        """
        Controls the speed and direction of the right motor (B).
        speed: -100 (Reverse) to 100 (Forward)
        """
        speed = max(min(speed, 100), -100)

        if speed > 0:
            GPIO.output(self.BIN1, GPIO.HIGH)
            GPIO.output(self.BIN2_PIN, GPIO.LOW)
            self.p_b.ChangeDutyCycle(speed)
        elif speed < 0:
            GPIO.output(self.BIN1, GPIO.LOW)
            GPIO.output(self.BIN2_PIN, GPIO.HIGH)
            self.p_b.ChangeDutyCycle(abs(speed))
        else:
            GPIO.output(self.BIN1, GPIO.HIGH)
            GPIO.output(self.BIN2_PIN, GPIO.HIGH)
            self.p_b.ChangeDutyCycle(0)

    def stop_all(self):
        """Stops both motors."""
        self.set_left_motor(0)
        self.set_right_motor(0)

    def cleanup(self):
        """Cleans up GPIO resources."""
        print("Cleaning up GPIO...")
        self.stop_all()
        GPIO.output(self.STBY, GPIO.LOW) # Disable driver
        self.p_a.stop()
        self.p_b.stop()
        GPIO.cleanup()