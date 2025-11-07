# robot_modes.py
# This file contains the logic for different robot operation modes.

# --- MOTOR SPEED CONTROL ---
MAX_SPEED = 70 
# ---------------------------

# --- SERVO CONTROL ---
SERVO_STEP_DEGREE = 0.5    # How many degrees to move per frame when button is pressed
# ---------------------

def _clamp_value(value, min_val, max_val):
    """Clamps a value between min_val and max_val."""
    return max(min(value, max_val), min_val)

def handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl): 
    """
    Handles manual driving and servo turret control.
    """
    # --- Motor Control Logic ---
    x_axis_joy, y_axis_joy = joy_ctrl.get_axes()
    y_axis_joy = -y_axis_joy # Invert Y-axis (Up = Forward)
    
    base_speed = y_axis_joy * MAX_SPEED
    turn_speed = x_axis_joy * MAX_SPEED
    
    left_speed = base_speed + turn_speed
    right_speed = base_speed - turn_speed
    
    left_speed = _clamp_value(left_speed, -MAX_SPEED, MAX_SPEED)
    right_speed = _clamp_value(right_speed, -MAX_SPEED, MAX_SPEED)
    
    motor_ctrl.set_left_motor(left_speed)
    motor_ctrl.set_right_motor(right_speed)

    # --- Servo Control Logic ---
    # X button: Tilt Up
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_X):
        new_tilt_angle = servo_ctrl.current_tilt_angle + SERVO_STEP_DEGREE
        servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, new_tilt_angle) # [수정 사항 4]: smooth_set_angle 대신 set_angle 직접 호출
    
    # B button: Tilt Down
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_B):
        new_tilt_angle = servo_ctrl.current_tilt_angle - SERVO_STEP_DEGREE
        servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, new_tilt_angle) # [수정 사항 4]

    # Y button: Pan Left
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_Y):
        new_pan_angle = servo_ctrl.current_pan_angle - SERVO_STEP_DEGREE
        servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, new_pan_angle) # [수정 사항 4]
        
    # A button: Pan Right
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_A):
        new_pan_angle = servo_ctrl.current_pan_angle + SERVO_STEP_DEGREE
        servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, new_pan_angle) # [수정 사항 4]

    # Return a status message for printing
    return (f"[MANUAL] Motor L:{left_speed:5.0f} R:{right_speed:5.0f} | "
            f"Servo Pan:{servo_ctrl.current_pan_angle:3d} Tilt:{servo_ctrl.current_tilt_angle:3d}")

def handle_automatic_mode(motor_ctrl, servo_ctrl): 
    """
    Handles autonomous behavior. (Placeholder)
    This is where camera.py logic will be integrated.
    """
    motor_ctrl.stop_all() 
    
    # AI logic would go here, e.g., tracking a target
    # servo_ctrl.set_angle(...)

    return "[AUTO] Automatic mode active... (Motors stopped)"