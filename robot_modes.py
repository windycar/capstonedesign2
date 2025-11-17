# robot_modes.py
import time 

# --- Constants ---
MAX_SPEED = 70 
SERVO_STEP_DEGREE = 1.0 # For manual control (not directly used in auto aiming)
START_BUTTON_ID = 7 

# --- Global State (for sharing between functions/threads) ---
g_fire_detected_ai = False
g_fire_detected_sensor = False
g_gas_detected = False
g_water_level = 100
g_pump_is_on = False # Keep track of pump state globally

# --- Auto Aiming Parameters ---
AIMING_TOLERANCE_X = 20 # Pixels: how close to center x-axis is "aimed"
AIMING_SPEED_PAN = 0.5 # Degrees per step for pan adjustment
AIMING_SPEED_TILT = 0.5 # Degrees per step for tilt adjustment

# --- Helper Functions ---
def _clamp_value(value, min_val, max_val):
    return max(min(value, max_val), min_val)

def handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl, pump_ctrl): 
    """
    Handles manual driving, servo turret, and pump control.
    Returns: status_message (str), pump_is_on (bool)
    """
    global g_pump_is_on # Update global pump state

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
        target_tilt += SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_B): 
        target_tilt -= SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_Y): 
        target_pan -= SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_A): 
        target_pan += SERVO_STEP_DEGREE
    
    # Apply angle limits and update servo
    servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, target_tilt)
    servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, target_pan)

    # --- Pump Control (L Button) ---
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_L):
        pump_ctrl.pump_on()
        g_pump_is_on = True
    else:
        pump_ctrl.pump_off()
        g_pump_is_on = False

    status_message = (f"[MANUAL] Motor L:{left_speed:5.0f} R:{right_speed:5.0f} | "
                      f"Servo Pan:{servo_ctrl.current_pan_angle:5.1f} Tilt:{servo_ctrl.current_tilt_angle:5.1f}")
    
    return status_message

def handle_automatic_mode(motor_ctrl, servo_ctrl, pump_ctrl, camera, detector, fire_sensor): 
    """
    Handles autonomous behavior including AI-based aiming and pump control.
    Returns: status_message (str)
    """
    global g_fire_detected_ai, g_fire_detected_sensor, g_pump_is_on
    
    motor_ctrl.stop_all() # For now, robot remains stationary in auto mode
    
    frame = camera.read()
    if frame is None:
        g_fire_detected_ai = False
        pump_ctrl.pump_off()
        g_pump_is_on = False
        return "[AUTO] Camera Frame Unavailable."

    h_frame, w_frame, _ = frame.shape
    center_x_frame = w_frame / 2
    center_y_frame = h_frame / 2

    # --- AI Inference ---
    boxes, confs, cids, _ = detector.infer(frame)
    
    # Assume the detector.draw_detections function now updates g_fire_detected_ai
    # and draws boxes directly on the frame (not returning a modified frame here)
    detector.draw_detections(frame, boxes, confs, cids) # This modifies the frame for GUI
    g_fire_detected_ai = (len(boxes) > 0) # Update global AI detection status

    status_message = "[AUTO] Patrolling..."
    
    if g_fire_detected_ai:
        # --- AI Aiming Logic ---
        # Find the largest/most confident fire (for now, just take the first detected)
        # In a more advanced system, you might track the fire or select closest.
        fire_box = boxes[0] 
        fire_x_center = (fire_box[0] + fire_box[2]) / 2
        fire_y_center = (fire_box[1] + fire_box[3]) / 2

        # Calculate deviation from frame center
        deviation_x = fire_x_center - center_x_frame
        deviation_y = fire_y_center - center_y_frame

        # Adjust Pan Servo
        current_pan = servo_ctrl.current_pan_angle
        if abs(deviation_x) > AIMING_TOLERANCE_X:
            if deviation_x > 0: # Fire is to the right of center
                servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, current_pan + AIMING_SPEED_PAN)
            else: # Fire is to the left of center
                servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, current_pan - AIMING_SPEED_PAN)
        
        # Adjust Tilt Servo (implement if needed, for simplicity focusing on Pan for now)
        # current_tilt = servo_ctrl.current_tilt_angle
        # if abs(deviation_y) > AIMING_TOLERANCE_Y:
        #     if deviation_y > 0: # Fire is below center
        #         servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, current_tilt - AIMING_SPEED_TILT)
        #     else: # Fire is above center
        #         servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, current_tilt + AIMING_SPEED_TILT)

        status_message = f"[AUTO] Fire Detected! Aiming... Pan:{servo_ctrl.current_pan_angle:.1f}"

        # --- Pump Control (after aiming check) ---
        # Only activate pump if fire is reasonably centered AND flame sensor confirms
        if abs(deviation_x) <= AIMING_TOLERANCE_X: # Assuming centered on X-axis is enough for pump
            _, g_fire_detected_sensor = fire_sensor.read_value() # Read digital flame sensor
            if g_fire_detected_sensor:
                pump_ctrl.pump_on()
                g_pump_is_on = True
                status_message += " - PUMP ON!"
            else:
                pump_ctrl.pump_off()
                g_pump_is_on = False
                status_message += " - Sensor not confirmed."
        else:
            pump_ctrl.pump_off() # Not aimed yet, or not confirmed
            g_pump_is_on = False

    else:
        # No AI fire detection
        pump_ctrl.pump_off()
        g_pump_is_on = False
        servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, servo_ctrl.CENTER_PAN_ANGLE) # Return to center
        servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, servo_ctrl.CENTER_TILT_ANGLE) # Return to center

    return status_message


def run_robot_loop(app_gui, motor_ctrl, joy_ctrl, servo_ctrl, pump_ctrl, 
                   camera, detector, fire_sensor, gas_sensor, water_sensor, buzzer, rgb_led): 
    """
    Runs the main robot operation loop.
    This function runs in a separate thread from the GUI.
    """
    global g_fire_detected_ai, g_fire_detected_sensor, g_gas_detected, g_water_level, g_pump_is_on
    
    manual_mode = False 
    start_button_pressed_last_frame = False
    
    print("[INFO] Robot control loop started.")
    print(f"Max motor speed set to {MAX_SPEED}%.")
    print("Press 'Start' button to toggle Manual/Automatic mode.")
    print("Press 'L' button to activate pump (Manual).")
    print("Press Ctrl+C to stop.")

    while app_gui.running: # Use GUI's running flag to control the loop
        
        # --- 1. Read All Global Sensors ---
        # water_level = water_sensor.read_level()
        # g_fire_detected_sensor = fire_sensor.read_value()[1] # Assuming digital read
        # g_gas_detected = gas_sensor.read_value()[1] # Assuming digital read

        # Placeholder for actual sensor reads (replace with your sensor objects)
        g_water_level = water_sensor.read_level()
        _, g_fire_detected_sensor = fire_sensor.read_value() # Returns (value, is_detected)
        _, g_gas_detected = gas_sensor.read_value() # Returns (value, is_detected)
        
        # --- 2. Check for Mode Switch ---
        current_start_button_state = joy_ctrl.get_button_state(START_BUTTON_ID)
        if current_start_button_state and not start_button_pressed_last_frame:
            manual_mode = not manual_mode
            print(f"\n*** MODE SWITCHED: {'MANUAL' if manual_mode else 'AUTOMATIC'} ***")
            motor_ctrl.stop_all() 
            pump_ctrl.pump_off() 
            g_pump_is_on = False # Reset pump state
            if manual_mode:
                camera.stop() # Turn camera OFF in manual mode
            else:
                camera.start() # Turn camera ON in auto mode for AI detection
            
            # Reset servo to center on mode switch
            servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, servo_ctrl.CENTER_PAN_ANGLE)
            servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, servo_ctrl.CENTER_TILT_ANGLE)

        start_button_pressed_last_frame = current_start_button_state

        # --- 3. Execute Mode-Specific Logic ---
        status_message = ""
        if manual_mode:
            status_message = handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl, pump_ctrl)
        else:
            status_message = handle_automatic_mode(motor_ctrl, servo_ctrl, pump_ctrl, camera, detector, fire_sensor)

        # --- 4. Handle Special Situations (Overrides for Buzzer/LED) ---
        if g_gas_detected:
            # Priority 1: Gas Detected (Highest)
            rgb_led.set_siren_effect() # 소방차 라이트
            buzzer.buzz_on()           # 삐이이이이 (연속)
        elif g_pump_is_on:
            # Priority 2: Pump is On (Water spraying)
            buzzer.beep_biyong()       # 삐용삐용
            if manual_mode:
                rgb_led.set_manual_mode() # 파란색 (물 쏠 때도 모드 색상 유지)
            else:
                rgb_led.set_auto_mode()   # 초록색 (물 쏠 때도 모드 색상 유지)
        else:
            # Priority 3: Normal Mode (No gas, no pump)
            buzzer.buzz_off()          # 부저 끄기
            if manual_mode:
                rgb_led.set_manual_mode() # 파란색
            else:
                rgb_led.set_auto_mode()   # 초록색
        
        # --- 5. Update GUI (Thread-safe) ---
        sensor_data = {
            'water': g_water_level,
            'flame': g_fire_detected_sensor,
            'gas': g_gas_detected,
            'pump_on': g_pump_is_on # Pass pump state to GUI for display if needed
        }
        app_gui.update_robot_state(manual_mode, sensor_data, g_fire_detected_ai)
        
        print(status_message, end='\r')
        time.sleep(0.005) # Maintain fast loop for joystick/motor control
    
    print("[INFO] Robot control loop stopped.")