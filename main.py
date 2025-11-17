# main.py
import threading
import argparse
import RPi.GPIO as GPIO # We need this for cleanup in case of crash
import time

# Import all our modules
import robot_modes 
import motor
import joystick
import servo
import pump 
import camera
import detector
import app_gui
import mcp_adc
import gas_sensor
import water_sensor
import fire_sensor
import buzzer
import rgb_led

def parse_args():
    """Parses command line arguments."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=str, default="best.onnx", help="Path to ONNX model")
    ap.add_argument("--labels", type=str, default="fire", help="Comma-separated labels")
    ap.add_argument("--img", type=int, default=320, help="Inference image size")
    ap.add_argument("--skip", type=int, default=1, help="Frame skip for inference")
    # Add other args from cam_label_tester_best.py as needed
    return ap.parse_args()

def main():
    args = parse_args()
    
    # --- Controller Handles ---
    motor_ctrl = None
    joy_ctrl = None
    servo_ctrl = None
    pump_ctrl = None
    camera_ctrl = None
    detector_ctrl = None
    gui = None
    robot_thread = None
    adc_ctrl = None
    gas_ctrl = None
    water_ctrl = None
    fire_ctrl = None
    buzzer_ctrl = None
    rgb_ctrl = None
    
    try:
        print("Initializing robot components from main...")
        
        # --- Initialize Hardware Controllers (RPi.GPIO) ---
        # motor.py calls GPIO.setmode(GPIO.BCM)
        motor_ctrl = motor.MotorController()
        joy_ctrl = joystick.JoystickController()
        servo_ctrl = servo.ServoController()
        pump_ctrl = pump.PumpController() 
        buzzer_ctrl = buzzer.BuzzerController()
        rgb_ctrl = rgb_led.RGBLed()

        # --- Initialize Analog Sensors (SPI / MCP3208) ---
        adc_ctrl = mcp_adc.MCP3208()
        gas_ctrl = gas_sensor.GasSensor(adc_ctrl)
        water_ctrl = water_sensor.WaterSensor(adc_ctrl)
        fire_ctrl = fire_sensor.FireSensor(adc_ctrl)
        
        # --- Initialize AI and Camera ---
        # Camera must start AFTER RPi.GPIO setup if using GStreamer (we use picamera2, so it's fine)
        camera_ctrl = camera.Camera()
        detector_ctrl = detector.Detector(
            model_path=args.model,
            img_size=args.img,
            labels=[s.strip() for s in args.labels.split(",")]
        )
        
        # --- Initialize GUI (in Main Thread) ---
        gui = app_gui.FireTruckGUI(camera_ctrl, detector_ctrl, args)
        
        # --- Create Robot Control Thread ---
        robot_thread = threading.Thread(
            target=robot_modes.run_robot_loop,
            args=(
                gui, motor_ctrl, joy_ctrl, servo_ctrl, 
                pump_ctrl, camera_ctrl, detector_ctrl,
                fire_ctrl, gas_ctrl, water_ctrl,
                buzzer_ctrl, rgb_ctrl
            ),
            daemon=True 
        )
        gui.robot_thread = robot_thread 

        # --- Start Everything ---
        # Camera is started by robot_modes when switching to auto mode
        robot_thread.start() # Start robot logic loop
        gui.start_gui_loops() # Start GUI's internal loops
        
        print("[INFO] All systems started. Running GUI main loop...")
        gui.run() # This blocks the main thread until the GUI window is closed

    except KeyboardInterrupt:
        print("\nProgram stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("\nCleaning up resources from main...")
        
        if gui:
            gui.running = False # Tell threads to stop
            time.sleep(0.1) # Give threads time to exit loop

        # Hardware cleanup
        if camera_ctrl:
            camera_ctrl.stop()
        if adc_ctrl:
            adc_ctrl.cleanup()
        if buzzer_ctrl:
            buzzer_ctrl.cleanup()
        if rgb_ctrl:
            rgb_ctrl.cleanup()
        if pump_ctrl:
            pump_ctrl.cleanup()
        if servo_ctrl:
            servo_ctrl.cleanup()
        if motor_ctrl:
            motor_ctrl.cleanup() # This one calls GPIO.cleanup()
        if joy_ctrl:
            joy_ctrl.quit()
            
        print("Program terminated.")

if __name__ == "__main__":
    main()