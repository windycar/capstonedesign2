# robot_modes.py
import time

# --- Constants ---
MAX_SPEED = 30
SERVO_STEP_DEGREE = 1.0 
START_BUTTON_ID = 7 

# AI Threshold (60%)
AUTO_MIN_SCORE = 0.2

# Pump Duration (3 Seconds)
PUMP_DURATION = 3.0

# Tracking Gains
PAN_GAIN = 15.0 
TILT_GAIN = 15.0


NOZZLE_OFFSET_Y = 0.5


NOZZLE_OFFSET_X = -0.07

# ---------------------------------------------------------


g_offset_x = NOZZLE_OFFSET_X   
g_offset_y = NOZZLE_OFFSET_Y 
pump_start_time = 0.0

def _clamp_value(value, min_val, max_val):
    return max(min(value, max_val), min_val)

def handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl, pump_ctrl, rgb_ctrl, buzz_ctrl, camera):
    """
    [Manual Mode]
    - Camera: Shows everything > 50%
    """
    # 1. Draw UI (Low threshold for manual visibility)
    camera.detect(sensor_active=False, min_score=0.50)

    # 2. Pump & Effect
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_L):
        pump_ctrl.pump_on()
        buzz_ctrl.on()
        rgb_ctrl.blink_red_effect()
    else:
        pump_ctrl.pump_off()
        buzz_ctrl.off()
        rgb_ctrl.set_manual_mode() 

    # 3. Motor
    x_axis, y_axis = joy_ctrl.get_axes()
    y_axis = -y_axis 
    base_speed = y_axis * MAX_SPEED
    turn_speed = x_axis * MAX_SPEED
    
    left_speed = _clamp_value(base_speed + turn_speed, -MAX_SPEED, MAX_SPEED)
    right_speed = _clamp_value(base_speed - turn_speed, -MAX_SPEED, MAX_SPEED)
    
    motor_ctrl.set_left_motor(left_speed)
    motor_ctrl.set_right_motor(right_speed)

    # 4. Servo (Manual Control)
    t_pan = servo_ctrl.current_pan_angle
    t_tilt = servo_ctrl.current_tilt_angle
    
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_X): t_tilt += SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_B): t_tilt -= SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_Y): t_pan -= SERVO_STEP_DEGREE
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_A): t_pan += SERVO_STEP_DEGREE
    
    t_pan = _clamp_value(t_pan, 0, 180)
    t_tilt = _clamp_value(t_tilt, 0, 180)
    
    if t_tilt != servo_ctrl.current_tilt_angle:
        servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, t_tilt)
    if t_pan != servo_ctrl.current_pan_angle:
        servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, t_pan)

    return f"[MANUAL] Cam: ON | Motors: L{left_speed:.0f}/R{right_speed:.0f}"

def handle_automatic_mode(motor_ctrl, servo_ctrl, pump_ctrl, fire_sens, rgb_ctrl, buzz_ctrl, camera, joy_ctrl):
    """
    [Auto Mode]
    - Tracks fire with Manual Offset (Trim) Adjustment
    - Buttons X/B adjust Left/Right Offset
    - Buttons Y/A adjust Up/Down Offset
    """
    global pump_start_time, g_offset_x, g_offset_y

    motor_ctrl.stop_all()
    
    # --- Real-time Offset Adjustment (Trim) ---
   
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_X): g_offset_x -= 0.005 # Left
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_B): g_offset_x += 0.005 # Right
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_Y): g_offset_y += 0.005 # Up
    if joy_ctrl.get_button_state(joy_ctrl.BUTTON_A): g_offset_y -= 0.005 # Down

    # Limit offsets
    g_offset_x = _clamp_value(g_offset_x, -0.3, 0.3)
    g_offset_y = _clamp_value(g_offset_y, -0.3, 0.3)
    
    # 1. Check Sensor & Time
    is_sensor_fire = fire_sens.is_fire_detected()
    current_time = time.time()
    
    # 2. Vision Detection (>60%)
    found, cx, cy = camera.detect(sensor_active=is_sensor_fire, min_score=AUTO_MIN_SCORE)
    
    # --- Pump Logic (3 Sec Hold) ---
    if found and is_sensor_fire:
        pump_start_time = current_time 

    time_since_start = current_time - pump_start_time
    is_shooting = time_since_start < PUMP_DURATION

    if is_shooting:
        pump_ctrl.pump_on()
        buzz_ctrl.on()
        rgb_ctrl.blink_red_effect()
        status_msg = f">>> SHOOTING! ({PUMP_DURATION - time_since_start:.1f}s) | Offset X:{g_offset_x:.2f} Y:{g_offset_y:.2f} <<<"
    else:
        pump_ctrl.pump_off()
        buzz_ctrl.off()
        if found:
            rgb_ctrl.set_color(1, 1, 0) 
            status_msg = f">>> Tracking... Offset[X:{g_offset_x:.2f} Y:{g_offset_y:.2f}] <<<"
        elif is_sensor_fire:
            rgb_ctrl.set_auto_mode()
            status_msg = ">>> SENSOR ACTIVE! (Searching...) <<<"
        else:
            rgb_ctrl.set_auto_mode()
            status_msg = f">>> Scanning... Offset[X:{g_offset_x:.2f} Y:{g_offset_y:.2f}] <<<"

    # 3. Visual Servoing (With Dynamic Offset)
    if found:
        # X Axis Target: Center(0.5) + Offset
        target_x = 0.5 + g_offset_x
        err_x = target_x - cx
        
        # Y Axis Target: Center(0.5) + Offset
        target_y = 0.5 + g_offset_y
        err_y = target_y - cy
        
        new_pan = servo_ctrl.current_pan_angle + (err_x * PAN_GAIN)
        new_tilt = servo_ctrl.current_tilt_angle + (err_y * TILT_GAIN)
        
        new_pan = _clamp_value(new_pan, 0, 180)
        new_tilt = _clamp_value(new_tilt, 0, 180)
        
        servo_ctrl.set_angle(servo_ctrl.PAN_SERVO_PIN, new_pan)
        servo_ctrl.set_angle(servo_ctrl.TILT_SERVO_PIN, new_tilt)

    return status_msg

def run_robot_loop(motor_ctrl, joy_ctrl, servo_ctrl, pump_ctrl, fire_sens, rgb_ctrl, buzz_ctrl, camera):
    manual_mode = False 
    last_start_btn = False
    
    print(">>> SYSTEM READY. Press START to switch modes. <<<")

    while True:
        curr_start = joy_ctrl.get_button_state(START_BUTTON_ID)
        if curr_start and not last_start_btn:
            manual_mode = not manual_mode
            print(f"\n*** MODE SWITCHED: {'MANUAL' if manual_mode else 'AUTO'} ***")
            motor_ctrl.stop_all() 
            pump_ctrl.pump_off()
            buzz_ctrl.off()
        last_start_btn = curr_start

        msg = ""
        if manual_mode:
            msg = handle_manual_mode(joy_ctrl, motor_ctrl, servo_ctrl, pump_ctrl, rgb_ctrl, buzz_ctrl, camera)
        else:
            msg = handle_automatic_mode(motor_ctrl, servo_ctrl, pump_ctrl, fire_sens, rgb_ctrl, buzz_ctrl, camera, joy_ctrl)

        print(msg, end='\r')
