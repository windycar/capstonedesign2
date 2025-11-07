# servo.py
import lgpio
import time
import numpy as np 

class ServoController:
    # --- [Previous code remains unchanged] ---
    PAN_SERVO_PIN = 24
    TILT_SERVO_PIN = 25
    PULSE_WIDTH_MIN = 500
    PULSE_WIDTH_MAX = 2500
    PWM_FREQ = 50
    INITIAL_PAN_ANGLE = 90
    INITIAL_TILT_ANGLE = 0

    def __init__(self):
        try:
            self.h = lgpio.gpiochip_open(0)
        except Exception as e:
            print(f"Error opening GPIO chip 0: {e}")
            print("Trying GPIO chip 4 (often for RPi 5)...")
            try:
                self.h = lgpio.gpiochip_open(4)
            except Exception as e2:
                print(f"Error opening GPIO chip 4: {e2}")
                print("Failed to initialize lgpio. Check permissions.")
                raise ConnectionError("Failed to open lgpio chip.")
        
        lgpio.gpio_claim_output(self.h, self.PAN_SERVO_PIN)
        lgpio.gpio_claim_output(self.h, self.TILT_SERVO_PIN)
        
        self.current_pan_angle = self.INITIAL_PAN_ANGLE
        self.current_tilt_angle = self.INITIAL_TILT_ANGLE
        
        print("ServoController initialized (using lgpio).")
        
        self.set_angle(self.PAN_SERVO_PIN, self.INITIAL_PAN_ANGLE)
        self.set_angle(self.TILT_SERVO_PIN, self.INITIAL_TILT_ANGLE)
        time.sleep(0.7)
        print(f"Servos initialized: Pan to {self.INITIAL_PAN_ANGLE} deg, Tilt to {self.INITIAL_TILT_ANGLE} deg.")

    def _angle_to_pulse_width(self, angle):
        angle = max(0, min(180, angle))
        pulse_width_us = int(self.PULSE_WIDTH_MIN + (angle / 180.0) * \
                          (self.PULSE_WIDTH_MAX - self.PULSE_WIDTH_MIN))
        return pulse_width_us

    def set_angle(self, servo_pin, angle):
        """Sets the angle of the specified servo instantly."""
        pulse_width_us = self._angle_to_pulse_width(angle)
        pulse_width_ns = pulse_width_us * 1000 # Convert to nanoseconds
        
        lgpio.tx_servo(self.h, servo_pin, pulse_width_ns, self.PWM_FREQ)
        
        if servo_pin == self.PAN_SERVO_PIN:
            self.current_pan_angle = angle
        elif servo_pin == self.TILT_SERVO_PIN:
            self.current_tilt_angle = angle



    def cleanup(self):
        """Stops servo pulses and disconnects from lgpio."""
        print("Cleaning up Servos...")
        lgpio.tx_servo(self.h, self.PAN_SERVO_PIN, 0, self.PWM_FREQ)
        lgpio.tx_servo(self.h, self.TILT_SERVO_PIN, 0, self.PWM_FREQ)
        
        lgpio.gpio_free(self.h, self.PAN_SERVO_PIN)
        lgpio.gpio_free(self.h, self.TILT_SERVO_PIN)
        
        lgpio.gpiochip_close(self.h)