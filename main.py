# main.py
import robot_modes 
import motor
import joystick
import servo
import pump 
import RPi.GPIO as GPIO 

def main():
    motor_ctrl = None
    joy_ctrl = None
    servo_ctrl = None
    pump_ctrl = None
    
    try:
        print("Initializing robot components from main...")
        motor_ctrl = motor.MotorController()
        joy_ctrl = joystick.JoystickController()
        servo_ctrl = servo.ServoController()
        pump_ctrl = pump.PumpController() # [FIX] Call without 'h' argument
        
        robot_modes.run_robot_loop(motor_ctrl, joy_ctrl, servo_ctrl, pump_ctrl)

    except KeyboardInterrupt:
        print("\nProgram stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("\nCleaning up resources from main...")
        
        # --- [CRITICAL FIX for TypeError] ---
        # Stop all PWM objects (pump, servo) *before*
        # motor_ctrl.cleanup() calls the final GPIO.cleanup().
        if pump_ctrl:
            pump_ctrl.cleanup()
        if servo_ctrl:
            servo_ctrl.cleanup()
        if motor_ctrl:
            motor_ctrl.cleanup() # This one calls GPIO.cleanup()
        # --- [END FIX] ---
            
        if joy_ctrl:
            joy_ctrl.quit()
            
        print("Program terminated.")

if __name__ == "__main__":
    main()
