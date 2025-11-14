# robot_modes.py
import time 

# --- [Previous code remains unchanged] ---
MAX_SPEED = 30
SERVO_STEP_DEGREE = 1.0
START_BUTTON_ID = 7 

def _clamp_value(value, min_val, max_val):
    return max(min(value, max_val), min_val)

def handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl, pump_ctrl): # pump_ctrl added
    """
    Handles manual driving, servo turret, and pump control.
    """
    # --- Motor Control Logic ---
    x_axis_joy, y_axis_joy = joy_ctrl.get_axes()
    y_axis_joy = -y_axis_joy 
    base_speed = y_axis_joy * MAX_SPEED
    turn_speed = x_axis_joy * MAX_SPEED
    left_speed = _clamp_value(base_speed + turn_speed, -MAX_SPEED, MAX_SPEED)
    right_speed = _clamp_value(base_speed - turn_speed, -MAX_SPEED, MAX_SPEED)
    motor_ctrl.set_left_motor(left_speed)
    motor_ctrl.set_right_motor(right_speed)

    # --- Servo Control Logic ---
    target_pan = servo_ctrl.current_pan_angle
    target_tilt = servo_ctrl.current_tilt_angle
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_X): 
        target_tilt = servo_ctrl.current_tilt_angle + SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_B): 
        target_tilt = servo_ctrl.current_tilt_angle - SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_Y): 
        target_pan = servo_ctrl.current_pan_angle - SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_A): 
        target_pan = servo_ctrl.current_pan_angle + SERVO_STEP_DEGREE
    if target_tilt != servo_ctrl.current_tilt_angle:
        servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, target_tilt)
    if target_pan != servo_ctrl.current_pan_angle:
        servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, target_pan)

    # --- [NEW] Pump Control Logic ---
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_L):
        pump_ctrl.pump_on()
    else:
        pump_ctrl.pump_off()
    # --- [END NEW] ---

    return (f"[MANUAL] Motor L:{left_speed:5.0f} R:{right_speed:5.0f} | "
            f"Servo Pan:{servo_ctrl.current_pan_angle:5.1f} Tilt:{servo_ctrl.current_tilt_angle:5.1f}")

def handle_automatic_mode(motor_ctrl, servo_ctrl, pump_ctrl): # pump_ctrl added
    """
    Handles autonomous behavior. (Placeholder)
    """
    motor_ctrl.stop_all() 
    # AI logic will call pump_ctrl.pump_on() when fire is confirmed
    # pump_ctrl.pump_off() 
    
    return "[AUTO] Automatic mode active... (Motors stopped)"

def run_robot_loop(motor_ctrl, joy_ctrl, servo_ctrl, pump_ctrl): # pump_ctrl added
    """
    Runs the main robot operation loop.
    """
    manual_mode = False 
    start_button_pressed_last_frame = False
    
    print(f"Max motor speed set to {MAX_SPEED}%.")
    print("Press 'Start' button to toggle Manual/Automatic mode.")
    print("Press 'L' button to activate pump (Manual).")
    print("Press Ctrl+C to stop.")

    while True:
        # Check for mode switch
        current_start_button_state = joy_ctrl.get_button_state(START_BUTTON_ID)
        if current_start_button_state and not start_button_pressed_last_frame:
            manual_mode = not manual_mode
            print(f"\n*** MODE SWITCHED: {'MANUAL' if manual_mode else 'AUTOMATIC'} ***")
            motor_ctrl.stop_all() 
            pump_ctrl.pump_off() # Stop pump on mode switch
        start_button_pressed_last_frame = current_start_button_state

        # Execute logic based on mode
        status_message = ""
        if manual_mode:
            status_message = handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl, pump_ctrl)
        else:
            status_message = handle_automatic_mode(motor_ctrl, servo_ctrl, pump_ctrl)

        print(status_message, end='\r')
        time.sleep(0.005)
