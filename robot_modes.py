# robot_modes.py
import time
import math

class RobotState:
    def __init__(self):
        self.current_mode = "automatic" # "automatic", "manual"
        self.fire_detected_ai = False
        self.fire_detected_sensor = False
        self.gas_detected_sensor = False
        self.water_level = 100
        self.pump_is_on = False
        # Add other states as needed

class RobotController:
    def __init__(self, motor_ctrl, servo_ctrl, pump_ctrl, buzzer_ctrl, rgb_led,
                 water_sensor, gas_sensor, fire_sensor, joystick_ctrl, gui_updater,
                 camera_ctrl, detector_ctrl, args):
        self.motor_ctrl = motor_ctrl
        self.servo_ctrl = servo_ctrl
        self.pump_ctrl = pump_ctrl
        self.buzzer_ctrl = buzzer_ctrl
        self.rgb_led = rgb_led
        self.water_sensor = water_sensor
        self.gas_sensor = gas_sensor
        self.fire_sensor = fire_sensor
        self.joystick_ctrl = joystick_ctrl
        self.gui_updater = gui_updater
        self.camera_ctrl = camera_ctrl # Can be None
        self.detector_ctrl = detector_ctrl # Can be None
        self.args = args

        self.robot_state = RobotState()
        self.running = True # Flag to control the loop

        self.last_sensor_read_time = time.time()
        self.sensor_read_interval = 0.5 # Read sensors twice per second

        self.target_pan = 90
        self.target_tilt = 90
        self.pan_speed = 5
        self.tilt_speed = 5

        self.patrol_state = 0 # 0: Moving forward, 1: Turning
        self.patrol_turn_start_time = 0
        self.patrol_turn_duration = 1.0 # Duration to turn (seconds)
        self.patrol_move_duration = 3.0 # Duration to move forward (seconds)
        self.last_patrol_action_time = time.time()

        self.fire_extinguish_state = 0 # 0: find, 1: approach, 2: extinguish
        self.last_fire_action_time = time.time()

    def stop_all_movement(self):
        self.motor_ctrl.stop()
        self.pump_ctrl.stop()
        self.rgb_led.set_color(0, 0, 0) # Turn off LEDs
        self.buzzer_ctrl.off()

    def read_sensors(self):
        self.robot_state.water_level = self.water_sensor.get_water_level()
        self.robot_state.gas_detected_sensor = self.gas_sensor.is_gas_detected()
        self.robot_state.fire_detected_sensor = self.fire_sensor.is_fire_detected()

        # For demonstration: if water level is 0, pump is off
        if self.robot_state.water_level == 0:
            self.pump_ctrl.stop()
            self.robot_state.pump_is_on = False

        # Simulate AI fire detection for GUI if detector is not available
        if not self.detector_ctrl:
            # If no AI, AI fire status mirrors flame sensor for GUI demo
            self.robot_state.fire_detected_ai = self.robot_state.fire_detected_sensor
        
    def handle_manual_mode(self):
        self.robot_state.current_mode = "manual"
        # Joystick control for motors
        left_axis = self.joystick_ctrl.get_axis(1) # Left stick Y-axis (vertical)
        right_axis = self.joystick_ctrl.get_axis(4) # Right stick Y-axis (vertical)
        
        # Assuming Y-axis is inverted for forward/backward movement
        left_power = -left_axis * 100 
        right_power = -right_axis * 100

        # Small dead zone
        dead_zone = 5
        if abs(left_power) < dead_zone: left_power = 0
        if abs(right_power) < dead_zone: right_power = 0

        self.motor_ctrl.set_left_motor(left_power)
        self.motor_ctrl.set_right_motor(right_power)

        # Joystick control for servo
        pan_axis = self.joystick_ctrl.get_axis(0) # Left stick X-axis
        tilt_axis = self.joystick_ctrl.get_axis(3) # Right stick X-axis
        
        # Adjust target_pan/tilt based on joystick input
        if abs(pan_axis) > 0.1:
            self.target_pan += pan_axis * self.pan_speed
        if abs(tilt_axis) > 0.1:
            self.target_tilt -= tilt_axis * self.tilt_speed # Invert for intuitive control
        
        self.target_pan = max(0, min(180, self.target_pan))
        self.target_tilt = max(0, min(180, self.target_tilt))
        self.servo_ctrl.set_pan_angle(self.target_pan)
        self.servo_ctrl.set_tilt_angle(self.target_tilt)

        # Joystick control for pump (Button A - index 0, Button B - index 1)
        if self.joystick_ctrl.get_button(0): # A button
            if not self.robot_state.pump_is_on and self.robot_state.water_level > 0:
                self.pump_ctrl.start()
                self.rgb_led.set_color(0, 0, 255) # Blue for pump on
                self.robot_state.pump_is_on = True
        elif self.joystick_ctrl.get_button(1): # B button
            if self.robot_state.pump_is_on:
                self.pump_ctrl.stop()
                self.rgb_led.set_color(0, 0, 0)
                self.robot_state.pump_is_on = False
        
        # Update AI fire status from detector if available (for manual mode display)
        if self.camera_ctrl and self.detector_ctrl:
            frame = self.camera_ctrl.read()
            if frame is not None:
                boxes, confs, cids, _ = self.detector_ctrl.infer(frame)
                self.robot_state.fire_detected_ai = any(cid == 0 for cid in cids) # Assuming class 0 is fire

        self.rgb_led.set_color(0, 0, 0) # Manual mode default LED off

    def handle_automatic_mode(self):
        self.robot_state.current_mode = "automatic"
        self.rgb_led.set_color(0, 255, 0) # Green for automatic mode

        # Always stop pump in auto mode if no fire detected
        if not self.robot_state.fire_detected_ai and not self.robot_state.fire_detected_sensor and self.robot_state.pump_is_on:
            self.pump_ctrl.stop()
            self.robot_state.pump_is_on = False

        if self.robot_state.gas_detected_sensor:
            print("Gas detected! Stopping and sounding alarm.")
            self.stop_all_movement()
            self.buzzer_ctrl.on()
            self.rgb_led.set_color(255, 0, 0) # Red for gas
            return

        if self.robot_state.fire_detected_ai or self.robot_state.fire_detected_sensor:
            if self.robot_state.water_level == 0:
                print("Fire detected but no water! Sounding alarm and stopping.")
                self.stop_all_movement()
                self.buzzer_ctrl.on()
                self.rgb_led.set_color(255, 0, 0) # Red for no water
                return
            
            # Fire extinguishing logic
            print("Fire detected! Initiating extinguishing sequence.")
            self.extinguish_fire_sequence()
            self.rgb_led.set_color(255, 165, 0) # Orange for fire fighting
            self.buzzer_ctrl.off() # Turn off buzzer if actively fighting fire
            return
        
        # If no gas and no fire, patrol
        self.buzzer_ctrl.off()
        self.patrol_mode()
        self.rgb_led.set_color(0, 255, 0) # Green for patrolling

    def extinguish_fire_sequence(self):
        # This is a placeholder for a more complex fire fighting logic
        # For now, it will just turn on the pump and stop movement
        self.motor_ctrl.stop()
        if not self.robot_state.pump_is_on and self.robot_state.water_level > 0:
            self.pump_ctrl.start()
            self.robot_state.pump_is_on = True

        # In a real scenario, you would use AI to aim the servo here
        # For now, just set to a default angle (e.g., straight ahead)
        self.servo_ctrl.set_pan_angle(90)
        self.servo_ctrl.set_tilt_angle(90)

    def patrol_mode(self):
        current_time = time.time()

        if self.patrol_state == 0: # Move forward
            self.motor_ctrl.set_left_motor(50)
            self.motor_ctrl.set_right_motor(50)
            if current_time - self.last_patrol_action_time > self.patrol_move_duration:
                self.patrol_state = 1
                self.patrol_turn_start_time = current_time
        elif self.patrol_state == 1: # Turn
            self.motor_ctrl.set_left_motor(50) # Turn right (left wheel forward, right wheel backward for pivot)
            self.motor_ctrl.set_right_motor(-50)
            if current_time - self.patrol_turn_start_time > self.patrol_turn_duration:
                self.patrol_state = 0
                self.last_patrol_action_time = current_time

    def set_running(self, status):
        self.running = status

def robot_loop(motor_ctrl, servo_ctrl, pump_ctrl, buzzer_ctrl, rgb_led, 
               water_sensor, gas_sensor, fire_sensor, joystick_ctrl, gui_updater,
               camera_ctrl, detector_ctrl, args):
    
    robot = RobotController(motor_ctrl, servo_ctrl, pump_ctrl, buzzer_ctrl, rgb_led, 
                            water_sensor, gas_sensor, fire_sensor, joystick_ctrl, gui_updater,
                            camera_ctrl, detector_ctrl, args)

    last_gui_update_time = time.time()
    gui_update_interval = 0.1 # Update GUI 10 times per second

    print("[INFO] Robot control loop started.")
    while robot.running:
        current_time = time.time()

        # Update joystick state
        if joystick_ctrl:
            joystick_ctrl.update()

        # Read sensors at a fixed interval
        if current_time - robot.last_sensor_read_time >= robot.sensor_read_interval:
            robot.read_sensors()
            robot.last_sensor_read_time = current_time

        # Mode switching logic
        if joystick_ctrl and joystick_ctrl.get_button(7): # START button (index 7 for Xbox)
            robot.robot_state.current_mode = "automatic"
        elif joystick_ctrl and joystick_ctrl.get_button(6): # BACK button (index 6 for Xbox)
            robot.robot_state.current_mode = "manual"
        
        if robot.robot_state.current_mode == "manual":
            robot.handle_manual_mode()
        else:
            robot.handle_automatic_mode()

        # Update GUI (thread-safe)
        if current_time - last_gui_update_time >= gui_update_interval:
            gui_updater(robot.robot_state.current_mode == "manual", 
                        {
                            'water': robot.robot_state.water_level,
                            'flame': robot.robot_state.fire_detected_sensor,
                            'gas': robot.robot_state.gas_detected_sensor,
                            'pump_on': robot.robot_state.pump_is_on
                        },
                        robot.robot_state.fire_detected_ai)
            last_gui_update_time = current_time

        time.sleep(0.05) # Small delay to prevent busy-waiting

    print("[INFO] Robot control loop stopped.")
