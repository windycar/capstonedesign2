# joystick.py
import pygame
import time

class JoystickController:
    DEADZONE = 0.1 # Joystick sensitivity deadzone

    # --- [NEW BUTTON MAP] ---
    # Based on your provided signal info
    BUTTON_B = 0
    BUTTON_A = 2
    BUTTON_Y = 1
    BUTTON_X = 3
    BUTTON_L = 4
    BUTTON_R = 5
    BUTTON_SELECT = 6
    START_BUTTON = 7 
    # ------------------------
    
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
        pygame.event.pump() 
        
        x_val = self.joystick.get_axis(0) if self.num_axes > 0 else 0.0
        y_val = self.joystick.get_axis(1) if self.num_axes > 1 else 0.0
        
        if abs(x_val) < self.DEADZONE:
            x_val = 0.0
        if abs(y_val) < self.DEADZONE:
            y_val = 0.0
            
        return x_val, y_val

    def get_button_state(self, button_id):
        pygame.event.pump() 
        
        if button_id >= self.num_buttons:
            return False
            
        return self.joystick.get_button(button_id) == 1

    def quit(self):
        """Quit Pygame"""
        print("Quitting Pygame.")
        pygame.quit()