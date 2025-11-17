# main.py
import pygame
import time
import threading
import argparse

# Robot Component Imports
from motor import MotorController
from servo import ServoController
from pump import PumpController
from buzzer import BuzzerController
from rgb_led import RGBLed
from mcp_adc import MCP3208
from water_sensor import WaterSensor
from gas_sensor import GasSensor
from fire_sensor import FireSensor
# from camera import Camera
# from detector import Detector

import app_gui
import robot_modes
from joystick import JoystickController

def main(args):
    pygame.init()
    pygame.joystick.init()

    # Initialize robot components
    print("Initializing robot components from main...")
    motor_ctrl = MotorController()
    
    joystick_ctrl = JoystickController()
    if joystick_ctrl.joysticks:
        print(f"Joystick '{joystick_ctrl.joysticks[0].get_name()}' initialized.")
        print(f"Axes: {joystick_ctrl.joysticks[0].get_numaxes()}, Buttons: {joystick_ctrl.joysticks[0].get_numbuttons()}")
    else:
        print("No joystick found. Please connect a joystick.")

    servo_ctrl = ServoController()
    pump_ctrl = PumpController()
    buzzer_ctrl = BuzzerController()
    rgb_led = RGBLed()

    # Initialize MCP3208 ADC
    adc_ctrl = MCP3208()
    print("MCP3208 ADC Initialized.")

    # Initialize Sensors
    water_sensor = WaterSensor(adc_ctrl, channel=0)
    print("WaterSensor Initialized.")
    gas_sensor = GasSensor(gpio_pin=2, adc_ctrl=adc_ctrl, channel=1)
    print("GasSensor Initialized.")
    fire_sensor = FireSensor(gpio_pin=3, adc_ctrl=adc_ctrl, channel=2)
    print("FireSensor Initialized.")
    
    # Camera and Detector are not used if camera is removed
    camera_ctrl = None
    detector_ctrl = None

    # Create GUI instance
    gui = app_gui.FireTruckGUI(camera_ctrl, detector_ctrl, args)

    # Create robot modes thread
    robot_modes_thread = threading.Thread(
        target=robot_modes.robot_loop,
        args=(motor_ctrl, servo_ctrl, pump_ctrl, buzzer_ctrl, rgb_led, 
              water_sensor, gas_sensor, fire_sensor, joystick_ctrl, 
              gui.update_robot_state, camera_ctrl, detector_ctrl, args)
    )
    gui.set_robot_thread(robot_modes_thread)

    try:
        robot_modes_thread.start()
        gui.start_gui_loops()
        gui.run()
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Cleaning up resources from main...")
        if adc_ctrl:
            adc_ctrl.close()
            print("MCP3208 ADC closed.")
        pump_ctrl.cleanup()
        servo_ctrl.cleanup()
        motor_ctrl.cleanup()
        pygame.quit()
        print("Quitting Pygame.")
        robot_modes_thread.join(timeout=2)
        print("Program terminated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fire Truck Robot Control System")
    parser.add_argument('--headless', action='store_true', help='Run without GUI')
    parser.add_argument('--res', type=str, default='800x450', help='Resolution for camera (e.g., 640x480)')
    parser.add_argument('--fps', type=int, default=30, help='Camera FPS')
    parser.add_argument('--skip', type=int, default=2, help='Skip frames for inference (e.g., 2 means infer every 3rd frame)')
    args = parser.parse_args()
    
    main(args)