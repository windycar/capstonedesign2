# app_gui.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import time
import threading 

class FireTruckGUI:
    def __init__(self, camera_ctrl, detector_ctrl, args):
        self.args = args
        self.camera_ctrl = camera_ctrl
        self.detector_ctrl = detector_ctrl
        self.robot_thread = None 
        
        self.running = True 
        self.manual_mode = False 
        
        self.fire_detected_ai = False
        self.fire_detected_sensor = False
        self.gas_detected_sensor = False
        self.water_level = 100 
        self.pump_is_on = False 

        self.tank_empty = False
        self.tank_blink_on = False 

        self.last_overlay_frame = None 
        self.infer_ms = 0.0
        self.fps_ema = 0.0
        self.frame_id = 0

        self.root = tk.Tk()
        self.root.title("Fire Truck GUI (YOLOv8n)")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_ui()
        
        print("[INFO] GUI initialized.")

    def _build_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        self.truck_status_label = ttk.Label(top_frame, text="Robot Status: Initializing...", foreground="blue", font=("Arial", 12, "bold"))
        self.truck_status_label.pack(side="left", padx=20)

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

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)
        self.ai_fire_label = ttk.Label(status_frame, text="AI Fire: None", background="#dddddd", anchor="center")
        self.ai_fire_label.pack(side="left", expand=True, fill="x", padx=2)
        self.flame_sensor_label = ttk.Label(status_frame, text="Flame Sensor: None", background="#dddddd", anchor="center")
        self.flame_sensor_label.pack(side="left", expand=True, fill="x", padx=2)
        self.gas_sensor_label = ttk.Label(status_frame, text="Gas Sensor: OK", background="#dddddd", anchor="center")
        self.gas_sensor_label.pack(side="left", expand=True, fill="x", padx=2)

        cam_frame = ttk.Frame(self.root)
        cam_frame.pack(fill="both", expand=True, padx=10, pady=5)
        # Always show Camera OFF, as camera_ctrl is None
        self.cam_label = ttk.Label(cam_frame, text="Camera OFF (Removed)", font=("Arial", 20))
        self.cam_label.pack(fill="both", expand=True)

    def start_gui_loops(self):
        self.root.after(500, self.blink_tank_loop)
        # No _display_loop call if camera_ctrl is None, as nothing to display
        if self.camera_ctrl:
            self.root.after(1, self._display_loop) 

    def _display_loop(self):
        if not self.running:
            return 
        
        # This loop should only run if camera_ctrl is not None
        if not self.camera_ctrl:
            self.cam_label.config(text="Camera OFF (Removed)", image='', background="black", foreground="white")
            return

        t0 = time.time()
        frame = self.camera_ctrl.read()
        
        if frame is None:
            self.cam_label.config(text="Camera Loading...", image='', background="black", foreground="white")
            self.root.after(100, self._display_loop)
            return

        self.cam_label.config(background="SystemButtonFace", foreground="black")
        
        do_infer = (self.frame_id % (self.args.skip + 1) == 0)
        
        if self.detector_ctrl and do_infer:
            boxes, confs, cids, self.infer_ms = self.detector_ctrl.infer(frame)
            frame, _ = self.detector_ctrl.draw_detections(frame, boxes, confs, cids)
            self.last_overlay_frame = frame
        else:
            if self.last_overlay_frame is not None:
                frame = self.last_overlay_frame
        
        t_now = time.time()
        fps = 1.0 / max(1e-6, (t_now - t0))
        self.fps_ema = self.fps_ema * 0.9 + fps * 0.1
        cv2.putText(frame, f"FPS:{self.fps_ema:.1f} infer:{self.infer_ms:.1f}ms", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img_pil)
        
        self.cam_label.imgtk = imgtk
        self.cam_label.configure(image=imgtk, text="")

        self.frame_id += 1
        self.root.after(10, self._display_loop)

    def update_robot_state(self, manual_mode, sensor_data, ai_fire_status):
        self.root.after(0, self._safe_state_update, manual_mode, sensor_data, ai_fire_status)

    def _safe_state_update(self, manual_mode, sensor_data, ai_fire_status):
        if not self.running: return 
        
        self.manual_mode = manual_mode
        self.fire_detected_ai = ai_fire_status

        self.water_level = sensor_data.get('water', 0)
        self.fire_detected_sensor = sensor_data.get('flame', False)
        self.gas_detected_sensor = sensor_data.get('gas', False)
        self.pump_is_on = sensor_data.get('pump_on', False)

        self.update_tank_gauge(self.water_level)
        self.update_sensor_status_labels()

    def update_tank_gauge(self, level_percent):
        level_percent = max(0, min(100, int(level_percent)))
        self.tank_empty = (level_percent == 0)

        if not self.tank_empty:
            filled_blocks = (level_percent + 9) // 10 
            for i, rect in enumerate(self.tank_blocks):
                if i < filled_blocks:
                    self.tank_canvas.itemconfig(rect, fill="#2196F3", outline="#1565C0")
                else:
                    self.tank_canvas.itemconfig(rect, fill="#eeeeee", outline="#b0b0b0")

    def blink_tank_loop(self):
        if not self.running: return 
        
        if self.tank_empty: 
            self.tank_blink_on = not self.tank_blink_on
            fill_color = "#ff4444" if self.tank_blink_on else "#ffeeee"
            outline_color = "#b00000"
            for rect in self.tank_blocks:
                self.tank_canvas.itemconfig(rect, fill=fill_color, outline=outline_color)
        
        self.root.after(400, self.blink_tank_loop)

    def update_sensor_status_labels(self):
        if self.fire_detected_ai:
            self.ai_fire_label.config(text="AI Fire: DETECTED", background="#ff4444", foreground="white")
        else:
            self.ai_fire_label.config(text="AI Fire: None", background="#dddddd", foreground="black")

        if self.fire_detected_sensor:
            self.flame_sensor_label.config(text="Flame Sensor: DETECTED", background="#ff9800", foreground="white")
        else:
            self.flame_sensor_label.config(text="Flame Sensor: None", background="#dddddd", foreground="black")

        if self.gas_detected_sensor:
            self.gas_sensor_label.config(text="Gas Sensor: DANGER", background="#ff7043", foreground="white")
        else:
            self.gas_sensor_label.config(text="Gas Sensor: OK", background="#dddddd", foreground="black")
            
        if self.gas_detected_sensor:
            self.truck_status_label.config(text="Robot Status: Gas Leak!", foreground="red", font=("Arial", 12, "bold"))
        elif self.fire_detected_ai or self.fire_detected_sensor:
            if self.pump_is_on:
                self.truck_status_label.config(text="Robot Status: Extinguishing Fire!", foreground="orange", font=("Arial", 12, "bold"))
            else:
                self.truck_status_label.config(text="Robot Status: Fire Detected!", foreground="orange", font=("Arial", 12, "bold"))
        elif self.tank_empty:
            self.truck_status_label.config(text="Robot Status: Low Water!", foreground="#cc0000", font=("Arial", 12, "bold"))
        elif self.manual_mode:
            self.truck_status_label.config(text="Robot Status: Manual Mode", foreground="blue")
        else:
            self.truck_status_label.config(text="Robot Status: Automatic Mode (Patrolling)", foreground="green")

    def on_close(self):
        print("[INFO] Close button pressed. Signaling all threads to stop...")
        self.running = False
        if self.robot_thread and self.robot_thread.is_alive():
            self.robot_thread.join(timeout=1.0)
        
        # Only stop camera if it was initialized
        if self.camera_ctrl:
            self.camera_ctrl.stop()
        self.root.destroy()
        print("[INFO] GUI closed.")

    def run(self):
        self.root.mainloop()

    def set_robot_thread(self, thread):
        self.robot_thread = thread