# main.py
import robot_modes
import motor
import joystick
import servo
import pump
import fire_sensor
import rgb_led
import buzzer
import camera
import time
import sys

def main():
    # Component Objects
    motor_ctrl = None
    joy_ctrl = None
    servo_ctrl = None
    pump_ctrl = None
    fire_sens = None
    rgb_ctrl = None
    buzz_ctrl = None
    cam_ctrl = None
    
    try:
        print("\n>>> SYSTEM INITIALIZATION START <<<")
        
        # 1. Initialize Hardware Controllers
        # Motor Controller (TB6612FNG)
        motor_ctrl = motor.MotorController()
        
        # Joystick (Pygame)
        joy_ctrl = joystick.JoystickController()
        
        # Servo Controller (Pan/Tilt)
        servo_ctrl = servo.ServoController()
        
        # Pump Controller
        pump_ctrl = pump.PumpController()
        
        # Fire Sensor (IR Flame Sensor)
        fire_sens = fire_sensor.FireSensor()
        
        # RGB LED & Buzzer
        rgb_ctrl = rgb_led.RGBController()
        buzz_ctrl = buzzer.BuzzerController()
        
        # 2. Initialize AI Camera
        # (This takes the longest, so we do it last)
        print(">>> Initializing AI Camera... Please wait.")
        cam_ctrl = camera.FireCamera() 
        
        # 3. Start Robot Control Loop
        print(">>> ALL SYSTEMS GO. Starting Main Loop... <<<")
        robot_modes.run_robot_loop(
            motor_ctrl, joy_ctrl, servo_ctrl, pump_ctrl, 
            fire_sens, rgb_ctrl, buzz_ctrl, cam_ctrl
        )

    except KeyboardInterrupt:
        print("\n>>> STOPPED BY USER (Ctrl+C) <<<")
        
    except Exception as e:
        print(f"\n>>> CRITICAL SYSTEM ERROR: {e} <<<")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n>>> CLEANING UP RESOURCES... <<<")
        # Cleanup in reverse order of dependency
        if pump_ctrl: pump_ctrl.cleanup()
        if servo_ctrl: servo_ctrl.cleanup()
        if rgb_ctrl: rgb_ctrl.cleanup()
        if buzz_ctrl: buzz_ctrl.cleanup()
        if cam_ctrl: cam_ctrl.cleanup()
        
        # Motor cleanup handles GPIO finalization
        if motor_ctrl: motor_ctrl.cleanup()
        
        if joy_ctrl: joy_ctrl.quit()
        print(">>> SYSTEM TERMINATED SAFELY <<<")

if __name__ == "__main__":
    main()