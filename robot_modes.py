# robot_modes.py
import time 

# --- Constants ---
MAX_SPEED = 70 
SERVO_STEP_DEGREE = 1.0
START_BUTTON_ID = 7 

def _clamp_value(value, min_val, max_val):
    return max(min(value, max_val), min_val)

def handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl, pump_ctrl): 
    """
    Handles manual driving and servo turret control.
    Returns: status_message (str), pump_is_on (bool)
    """
    # --- Motor Control ---
    x_axis_joy, y_axis_joy = joy_ctrl.get_axes()
    y_axis_joy = -y_axis_joy 
    base_speed = y_axis_joy * MAX_SPEED
    turn_speed = x_axis_joy * MAX_SPEED
    left_speed = _clamp_value(base_speed + turn_speed, -MAX_SPEED, MAX_SPEED)
    right_speed = _clamp_value(base_speed - turn_speed, -MAX_SPEED, MAX_SPEED)
    motor_ctrl.set_left_motor(left_speed)
    motor_ctrl.set_right_motor(right_speed)

    # --- Servo Control ---
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

    # --- Pump Control (L Button) ---
    pump_is_on = False
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_L):
        pump_ctrl.pump_on()
        pump_is_on = True
    else:
        pump_ctrl.pump_off()

    status_message = (f"[MANUAL] Motor L:{left_speed:5.0f} R:{right_speed:5.0f} | "
                      f"Servo Pan:{servo_ctrl.current_pan_angle:5.1f} Tilt:{servo_ctrl.current_tilt_angle:5.1f}")
    
    return status_message, pump_is_on

def handle_automatic_mode(motor_ctrl, servo_ctrl, pump_ctrl): 
    """
    Handles autonomous behavior. (Placeholder)
    Returns: status_message (str), pump_is_on (bool)
    """
    motor_ctrl.stop_all() 
    
    # --- [NEW] AI Logic Placeholder ---
    # if (fire_detected_ai and fire_detected_sensor):
    #     pump_ctrl.pump_on()
    #     pump_is_on = True
    # else:
    #     pump_ctrl.pump_off()
    #     pump_is_on = False
    # ----------------------------------
    pump_is_on = False # Placeholder
    
    return "[AUTO] Automatic mode active... (Motors stopped)", pump_is_on

def run_robot_loop(motor_ctrl, joy_ctrl, servo_ctrl, pump_ctrl, 
                   gas_sensor, water_sensor, buzzer, rgb_led): 
    """
    Runs the main robot operation loop.
    (Removed other sensors for this specific request)
    """
    manual_mode = False 
    start_button_pressed_last_frame = False
    
    print(f"Max motor speed set to {MAX_SPEED}%.")
    print("Press 'Start' button to toggle Manual/Automatic mode.")
    print("Press 'L' button to activate pump (Manual).")
    print("Press Ctrl+C to stop.")

    while True:
        # --- 1. Read Global Sensors ---
        # g_gas_detected = gas_sensor.read_value()[1] # Assuming digital read
        g_gas_detected = False # Placeholder
        # g_water_level = water_sensor.read_level()
        g_water_level = 100 # Placeholder

        # --- 2. Check for Mode Switch ---
        current_start_button_state = joy_ctrl.get_button_state(START_BUTTON_ID)
        if current_start_button_state and not start_button_pressed_last_frame:
            manual_mode = not manual_mode
            print(f"\n*** MODE SWITCHED: {'MANUAL' if manual_mode else 'AUTOMATIC'} ***")
            motor_ctrl.stop_all() 
            pump_ctrl.pump_off() 
        start_button_pressed_last_frame = current_start_button_state

        # --- 3. Execute Mode-Specific Logic ---
        status_message = ""
        pump_is_on = False
        if manual_mode:
            status_message, pump_is_on = handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl, pump_ctrl)
        else:
            status_message, pump_is_on = handle_automatic_mode(motor_ctrl, servo_ctrl, pump_ctrl)

        # --- 4. [NEW] Handle Special Situations (Overrides) ---
        if g_gas_detected:
            # Priority 1: Gas Detected
            rgb_led.set_siren_effect() # 
            buzzer_ctrl.buzz_on()      # 
        elif pump_is_on:
            # Priority 2: Pump is On
            buzzer_ctrl.beep_biyong()  # 
            if manual_mode:
                rgb_led.set_manual_mode() # 
            else:
                rgb_led.set_auto_mode()   # 
        else:
            # Priority 3: Normal Mode
            buzzer_ctrl.buzz_off()     # 
            if manual_mode:
                rgb_led.set_manual_mode() # 
            else:
                rgb_led.set_auto_mode()   # 
        # --- [END NEW] ---

        print(status_message, end='\r')
        time.sleep(0.005)