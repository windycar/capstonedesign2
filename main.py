# main.py
import time
import motor
import joystick
import servo 
import robot_modes
# camera.py and speaker.py will be imported here later

# 8BitDo 'Start' button ID
START_BUTTON_ID = 7 

class Robot:
    """Main class to manage robot state and components."""
    
    def __init__(self):
        """Initialize all robot components."""
        print("Initializing robot components...")
        self.motor_ctrl = motor.MotorController()
        self.joy_ctrl = joystick.JoystickController()
        self.servo_ctrl = servo.ServoController() 
        
        # Add other components here later
        # self.camera = camera.Camera()
        # self.speaker = speaker.Speaker()
        
        self.manual_mode = False 
        self.start_button_pressed_last_frame = False
        self.running = True
        
        print(f"Max motor speed set to {robot_modes.MAX_SPEED}%.")
        print("Press 'Start' button to toggle Manual/Automatic mode.")
        print("Use Joystick for driving (Manual).")
        print("Use X/B for Tilt, Y/A for Pan (Manual).")
        print("Press Ctrl+C to stop.")

    def check_mode_switch(self):
        """Checks for 'Start' button press to toggle mode."""
        current_start_button_state = self.joy_ctrl.get_button_state(START_BUTTON_ID)
        
        if current_start_button_state and not self.start_button_pressed_last_frame:
            self.manual_mode = not self.manual_mode
            print(f"\n*** MODE SWITCHED: {'MANUAL' if self.manual_mode else 'AUTOMATIC'} ***")
            self.motor_ctrl.stop_all() 
            
        self.start_button_pressed_last_frame = current_start_button_state

    def loop(self):
        """Main robot loop."""
        while self.running:
            try:
                self.check_mode_switch()

                status_message = ""
                
                if self.manual_mode:
                    status_message = robot_modes.handle_manual_mode(self.joy_ctrl, self.motor_ctrl, self.servo_ctrl)
                else:
                    # Pass all components needed for auto mode
                    status_message = robot_modes.handle_automatic_mode(self.motor_ctrl, self.servo_ctrl)

                print(status_message, end='\r')
                time.sleep(0.05)
                
            except KeyboardInterrupt:
                print("\nProgram stopped by user (Ctrl+C).")
                self.running = False 
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                self.running = False 

    def cleanup(self):
        """Clean up all resources."""
        print("\nCleaning up resources...")
        if hasattr(self, 'motor_ctrl'):
            self.motor_ctrl.cleanup()
        if hasattr(self, 'joy_ctrl'):
            self.joy_ctrl.quit()
        if hasattr(self, 'servo_ctrl'):
            self.servo_ctrl.cleanup() 
        # Add cleanup for camera/speaker later
        print("Program terminated.")

def main():
    robot = None
    try:
        robot = Robot()
        robot.loop()
    finally:
        if robot:
            robot.cleanup()

if __name__ == "__main__":
    main()