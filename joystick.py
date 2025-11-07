# joystick.py
import pygame
import time

class JoystickController:
    DEADZONE = 0.1 # Joystick sensitivity deadzone

    # 8BitDo Controller Button IDs (Verify these!)
    # These IDs can vary based on connection mode (X-input/D-input).
    # You MUST verify these IDs using a button test script.
    BUTTON_A = 0 # 'A' button
    BUTTON_B = 1 # 'B' button
    BUTTON_X = 3 # 'X' button
    BUTTON_Y = 4 # 'Y' button
    START_BUTTON = 7 # 'Start' button
    
    def __init__(self):
        """Initialize Pygame and the joystick"""
        pygame.init()
        pygame.joystick.init()
        
        self.joystick_count = pygame.joystick.get_count()
        if self.joystick_count == 0:
            print("Error: No joystick found.")
            raise ConnectionError("No joystick found. Is 8BitDo connected?")
        
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        
        self.num_axes = self.joystick.get_numaxes()
        self.num_buttons = self.joystick.get_numbuttons()
            
        print(f"Joystick '{self.joystick.get_name()}' initialized.")
        print(f"Axes: {self.num_axes}, Buttons: {self.num_buttons}")

    def get_axes(self):
        """
        Get the X (Axis 0) and Y (Axis 1) values.
        Returns: (x_val, y_val), each between -1.0 and 1.0
        """
        pygame.event.pump() # Process event queue
        
        x_val = self.joystick.get_axis(0) if self.num_axes > 0 else 0.0
        y_val = self.joystick.get_axis(1) if self.num_axes > 1 else 0.0
        
        if abs(x_val) < self.DEADZONE:
            x_val = 0.0
        if abs(y_val) < self.DEADZONE:
            y_val = 0.0
            
        return x_val, y_val

    def get_button_state(self, button_id):
        """
        Get the state of a specific button.
        Returns: True (Pressed) or False (Not Pressed)
        """
        pygame.event.pump() 
        
        if button_id >= self.num_buttons:
            return False
            
        return self.joystick.get_button(button_id) == 1

    def quit(self):
        """Quit Pygame"""
        print("Quitting Pygame.")
        pygame.quit()