# app_gui.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import time

class FireTruckGUI:
    def __init__(self, camera_ctrl, detector_ctrl, args):
        self.args = args
        self.camera_ctrl = camera_ctrl # Camera object
        self.detector_ctrl = detector_ctrl # Detector object
        self.robot_thread = None # Placeholder for the robot thread
        
        # State variables
        self.running = False # Robot running state
        self.manual_mode = False # Robot operational mode
        self.fire_detected_ai = False
        self.flame_detected_sensor = False
        self.gas_detected_sensor = False
        self.water_level = 0
        self.tank_empty = True
        self.tank_blink_on = False
        self.last_overlay = None
        self.infer_ms = 0.0
        self.fps_ema = 0.0

        # Build the UI
        self.root = tk.Tk()
        self.root.title("Fire Truck GUI (YOLOv8n)")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_ui()
        
        print("[INFO] GUI initialized.")

    def _build_ui(self):
        # 1. Top Frame: Start/Stop Button + Status
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        self.run_button = ttk.Button(top_frame, text="소방차 운행 시작", command=self.toggle_run)
        self.run_button.pack(side="left")
        self.truck_status_label = ttk.Label(top_frame, text="소방차 상태: 정지", foreground="red", font=("Arial", 12, "bold"))
        self.truck_status_label.pack(side="left", padx=20)

        # 2. Water Tank Gauge
        tank_frame = ttk.Frame(self.root)
        tank_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(tank_frame, text="Water Tank Level").pack(anchor="w")
        self.tank_canvas = tk.Canvas(tank_frame, width=400, height=40, bg="white", highlightthickness=1, highlightbackground="black")
        self.tank_canvas.pack(fill="x", pady=5)
        self.tank_blocks = []
        block_w = 400 / 10
        for i in range(10):
            x1 = i * block_w + 2
            x2 = (i + 1) * block_w - 2
            rect = self.tank_canvas.create_rectangle(x1, 5, x2, 35, fill="#eeeeee", outline="#b0b0b0")
            self.tank_blocks.append(rect)

        # 3. Sensor Status Labels
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)
        self.cam_status_label = ttk.Label(status_frame, text="AI Fire: None", background="#dddddd", anchor="center")
        self.cam_status_label.pack(side="left", expand=True, fill="x", padx=2)
        self.flame_status_label = ttk.Label(status_frame, text="Flame Sensor: None", background="#dddddd", anchor="center")
        self.flame_status_label.pack(side="left", expand=True, fill="x", padx=2)
        self.gas_status_label = ttk.Label(status_frame, text="Gas Sensor: OK", background="#dddddd", anchor="center")
        self.gas_status_label.pack(side="left", expand=True, fill="x", padx=2)

        # 4. Camera View
        cam_frame = ttk.Frame(self.root)
        cam_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.cam_label = ttk.Label(cam_frame, text="Camera OFFLINE", font=("Arial", 20))
        self.cam_label.pack(fill="both", expand=True)

    def toggle_run(self):
        """Starts or stops the main robot thread."""
        self.running = not self.running
        if self.running:
            self.run_button.config(text="소방차 운행 중지")
            self.truck_status_label.config(text="소방차 상태: 자동 모드 대기", foreground="blue")
            
            # Start the robot control loop (from robot_modes.py)
            if self.robot_thread is None or not self.robot_thread.is_alive():
                print("[INFO] Starting robot control thread...")
                # We need main.py to start this thread and pass us the reference
                pass # Main.py will handle this
        else:
            self.run_button.config(text="소방차 운행 시작")
            self.truck_status_label.config(text="소방차 상태: 정지", foreground="red")
            print("[INFO] Stopping robot control thread...")
            # The robot_thread loop will see self.running == False and stop

    def start_gui_loops(self):
        """Starts the GUI's internal update loops."""
        self.root.after(500, self.blink_tank_loop)
        self.root.after(1, self._display_loop) # Start camera display loop

    def _display_loop(self):
        """Main loop for updating the camera feed in the GUI."""
        if not self.running:
            self.cam_label.config(text="Camera OFFLINE", image='') # Clear image
            self.last_overlay = None
            self.root.after(100, self._display_loop) # Check again later
            return
        
        t0 = time.time()
        frame = self.camera_ctrl.read()
        
        if frame is None:
            self.root.after(10, self._display_loop) # Wait for frame
            return

        # --- Manual Mode: Camera Off ---
        if self.manual_mode:
            self.cam_label.config(text="Camera OFF (Manual Mode)", image='', background="black", foreground="white")
            self.last_overlay = None
        
        # --- Automatic Mode: Camera On ---
        else:
            self.cam_label.config(background="SystemButtonFace", foreground="black") # Reset background
            do_infer = (self.frame_id % (self.args.skip + 1) == 0)
            
            if do_infer:
                boxes, confs, cids, self.infer_ms = self.detector_ctrl.infer(frame)
                frame, self.fire_detected_ai = self.detector_ctrl.draw_detections(frame, boxes, confs, cids)
                self.last_overlay = (frame, self.fire_detected_ai)
            else:
                if self.last_overlay:
                    frame, self.fire_detected_ai = self.last_overlay[0].copy(), self.last_overlay[1]
            
            # Draw performance stats
            t_now = time.time()
            fps = 1.0 / max(1e-6, (t_now - t0))
            self.fps_ema = self.fps_ema * 0.9 + fps * 0.1
            cv2.putText(frame, f"FPS:{self.fps_ema:.1f} infer:{self.infer_ms:.1f}ms", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Convert frame for Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img_pil)
            
            self.cam_label.imgtk = imgtk
            self.cam_label.configure(image=imgtk, text="")

        self.frame_id += 1
        self.root.after(10, self._display_loop) # ~100Hz refresh rate

    def update_robot_state(self, manual_mode, sensor_data):
        """Thread-safe method to update GUI from the robot thread."""
        # Use root.after to safely update Tkinter widgets from another thread
        self.root.after(0, self._safe_state_update, manual_mode, sensor_data)

    def _safe_state_update(self, manual_mode, sensor_data):
        """Internal method executed by the GUI thread."""
        self.manual_mode = manual_mode
        
        # Unpack sensor data (assuming sensor_data is a dictionary)
        self.water_level = sensor_data.get('water', 0)
        self.flame_detected_sensor = sensor_data.get('flame', False)
        self.gas_detected_sensor = sensor_data.get('gas', False)

        # Update labels
        self.update_tank_gauge(self.water_level)
        self.update_sensor_status_labels()

    def update_tank_gauge(self, level_percent):
        """Updates the water tank gauge visual."""
        level_percent = max(0, min(100, int(level_percent)))
        self.tank_empty = (level_percent == 0)

        if not self.tank_empty:
            filled_blocks = (level_percent + 9) // 10 # Calculate filled blocks (1-10)
            for i, rect in enumerate(self.tank_blocks):
                if i < filled_blocks:
                    self.tank_canvas.itemconfig(rect, fill="#2196F3", outline="#1565C0")
                else:
                    self.tank_canvas.itemconfig(rect, fill="#eeeeee", outline="#b0b0b0")

    def blink_tank_loop(self):
        """Blinks the tank gauge red if empty."""
        if self.tank_empty:
            self.tank_blink_on = not self.tank_blink_on
            fill_color = "#ff4444" if self.tank_blink_on else "#ffeeee"
            outline_color = "#b00000"
            for rect in self.tank_blocks:
                self.tank_canvas.itemconfig(rect, fill=fill_color, outline=outline_color)
        
        if self.running: # Only loop if running
            self.root.after(400, self.blink_tank_loop)

    def update_sensor_status_labels(self):
        """Updates the text and color of sensor status labels."""
        # AI Fire Detection
        if self.fire_detected_ai:
            self.cam_status_label.config(text="AI Fire: DETECTED", background="#ff4444", foreground="white")
        else:
            self.cam_status_label.config(text="AI Fire: None", background="#dddddd", foreground="black")

        # Flame Sensor
        if self.flame_detected_sensor:
            self.flame_status_label.config(text="Flame Sensor: DETECTED", background="#ff9800", foreground="white")
        else:
            self.flame_status_label.config(text="Flame Sensor: None", background="#dddddd", foreground="black")

        # Gas Sensor
        if self.gas_detected_sensor:
            self.gas_status_label.config(text="Gas Sensor: DANGER", background="#ff7043", foreground="white")
        else:
            self.gas_status_label.config(text="Gas Sensor: OK", background="#dddddd", foreground="black")
            
        # Overall Truck Status
        if not self.running:
            self.truck_status_label.config(text="소방차 상태: 정지", foreground="red")
        elif self.gas_detected_sensor:
            self.truck_status_label.config(text="소방차 상태: 가스 누출!", foreground="red", font=("Arial", 12, "bold"))
        elif self.fire_detected_ai or self.flame_detected_sensor:
            self.truck_status_label.config(text="소방차 상태: 화재 대응 중!", foreground="orange", font=("Arial", 12, "bold"))
        elif self.manual_mode:
            self.truck_status_label.config(text="소방차 상태: 수동 조작 중", foreground="blue")
        else:
            self.truck_status_label.config(text="소방차 상태: 자동 모드 (순찰)", foreground="green")

    def on_close(self):
        """Handles window close event."""
        print("[INFO] Close button pressed. Stopping robot...")
        self.running = False # Signal robot thread to stop
        if self.robot_thread and self.robot_thread.is_alive():
            self.robot_thread.join(timeout=1.0) # Wait for robot thread
        
        self.camera_ctrl.stop() # Stop camera thread
        self.root.destroy()
        print("[INFO] GUI closed.")

    def run(self):
        """Starts the GUI main loop."""
        self.root.mainloop()