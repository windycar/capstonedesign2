# camera.py
import cv2
import numpy as np
import onnxruntime as ort
import os
import time

# [IMPORTANT] Using Native Camera Library for RPi 5
from picamera2 import Picamera2
import libcamera

class FireCamera:
    def __init__(self, model_filename="best_nano_320.onnx", width=640, height=480): #best.onnx,best_nano_320.onnx
        print("\n>>> [SYSTEM] LOADING CAMERA CODE (ACCURACY FILTER ADDED) <<<")
        
        self.img_size = 320
        self.conf_thres = 0.5 # Default threshold
        
        # 1. Automatic Path Detection
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, model_filename)
        
        # 2. Load AI Model
        self.session = None
        if os.path.exists(model_path):
            try:
                print(f"[Camera] Loading AI Model from: {model_path}")
                so = ort.SessionOptions()
                so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                self.session = ort.InferenceSession(model_path, sess_options=so, providers=["CPUExecutionProvider"])
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                print("[Camera] Model loaded successfully.")
            except Exception as e:
                print(f"[Camera] Model Load Error: {e}")
                self.session = None
        else:
            print(f"[Camera] Error: Model file not found at {model_path}")

        # 3. Initialize Picamera2 (RPi 5 Native)
        print("[Camera] Initializing Picamera2...")
        try:
            self.picam2 = Picamera2()
            
            cfg = self.picam2.create_video_configuration(
                main={"size": (width, height), "format": "RGB888"},
                transform=libcamera.Transform(hflip=True, vflip=True)
            )
            self.picam2.configure(cfg)
            self.picam2.start()
            print("[Camera] Camera started successfully via Picamera2.")
            
        except Exception as e:
            print(f"[Camera] Hardware Init Error: {e}")
            self.picam2 = None

    def _letterbox(self, im, new_shape):
        shape = im.shape[:2]
        r = min(new_shape[0]/shape[0], new_shape[1]/shape[1])
        new_unpad = int(round(shape[1]*r)), int(round(shape[0]*r))
        dw, dh = new_shape[1]-new_unpad[0], new_shape[0]-new_unpad[1]
        dw, dh = dw/2, dh/2
        
        if shape[::-1] != new_unpad:
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
            
        top, bottom = int(round(dh)), int(round(dh))
        left, right = int(round(dw)), int(round(dw))
        
        im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114,114,114))
        return im, r, (dw, dh)

    def read(self):
        if self.picam2:
            return self.picam2.capture_array("main")
        return None

    def detect(self, sensor_active=False, min_score=0.5):
        """
        [Updated] Now supports 'min_score' to filter weak detections.
        """
        if self.session is None or self.picam2 is None:
            return False, 0.5, 0.5

        try:
            frame_rgb = self.read() 
            if frame_rgb is None: return False, 0.5, 0.5
        except:
            return False, 0.5, 0.5

        # Preprocessing
        img, ratio, (dw, dh) = self._letterbox(frame_rgb, (self.img_size, self.img_size))
        img_input = cv2.cvtColor(img, cv2.COLOR_RGB2BGR).astype(np.float32)/255.0
        img_input = np.transpose(img_input, (2,0,1))[None,...]

        # Inference
        out = self.session.run([self.output_name], {self.input_name: img_input})[0]
        preds = np.squeeze(out, 0).T
        boxes = preds[:, :4]
        scores = preds[:, 4:]
        conf_max = scores.max(1)
        
        # [CORE LOGIC] Use the dynamic min_score provided by Robot Modes
        mask = conf_max > min_score
        
        boxes = boxes[mask]
        conf_max = conf_max[mask]

        found = False
        cx, cy = 0.5, 0.5

        display_frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        if len(boxes) > 0:
            best_idx = np.argmax(conf_max)
            bx, by, bw, bh = boxes[best_idx]
            cx = bx/self.img_size
            cy = by/self.img_size
            found = True
            
            x1 = int((bx - bw/2 - dw)/ratio)
            y1 = int((by - bh/2 - dh)/ratio)
            x2 = int((bx + bw/2 - dw)/ratio)
            y2 = int((by + bh/2 - dh)/ratio)
            
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0,0,255), 3)
            # Show score on screen
            cv2.putText(display_frame, f"FIRE: {conf_max[best_idx]:.2f}", (x1,y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        # UI Overlay
        vis_color = (0, 255, 0) if found else (0, 0, 255) 
        vis_text = f"VISION: [{'DETECTED' if found else 'SEARCHING'}] > {min_score*100:.0f}%"
        cv2.putText(display_frame, vis_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, vis_color, 2)

        sens_color = (0, 0, 255) if sensor_active else (0, 255, 0)
        sens_text = "SENSOR: [ FIRE!!! ]" if sensor_active else "SENSOR: [ SAFE ]"
        cv2.putText(display_frame, sens_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, sens_color, 2)

        cv2.imshow("Robot Vision", display_frame)
        cv2.waitKey(1)
        
        return found, cx, cy

    def cleanup(self):
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
        cv2.destroyAllWindows()
