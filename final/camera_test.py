# camera.py
import cv2
import numpy as np
import onnxruntime as ort
import os
import time

# [IMPORTANT] Native Camera Library for RPi 5
from picamera2 import Picamera2
import libcamera

class FireCamera:
    def __init__(self, model_filename="best_nano_320.onnx", width=640, height=480):
        print("\n>>> [SYSTEM] LOADING PICAMERA2 NATIVE MODE <<<")
        
        self.img_size = 320
        self.conf_thres = 0.5
        
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

        # 3. Initialize Picamera2 (The RPi 5 Native Way)
        print("[Camera] Initializing Picamera2...")
        try:
            self.picam2 = Picamera2()
            
            # Configure camera (RGB888 format is standard for processing)
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
        # Resize and pad image while maintaining aspect ratio
        shape = im.shape[:2]
        r = min(new_shape[0]/shape[0], new_shape[1]/shape[1])
        new_unpad = int(round(shape[1]*r)), int(round(shape[0]*r))
        dw, dh = new_shape[1]-new_unpad[0], new_shape[0]-new_unpad[1]
        dw, dh = dw/2, dh/2
        
        if shape[::-1] != new_unpad:
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
            
        top, bottom = int(round(dh)), int(round(dh))
        left, right = int(round(dw)), int(round(dw))
        
        # Add border (padding)
        im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114,114,114))
        return im, r, (dw, dh)

    def read(self):
        # Capture raw array from camera
        if self.picam2:
            return self.picam2.capture_array("main")
        return None

    def detect(self):
        # 1. Check Hardware
        if self.session is None or self.picam2 is None:
            return False, 0.5, 0.5

        # 2. Get Frame
        try:
            frame = self.read()
            if frame is None:
                return False, 0.5, 0.5
        except Exception as e:
            print(f"[Camera] Capture Error: {e}")
            return False, 0.5, 0.5

        # 3. Preprocessing
        try:
            img, ratio, (dw, dh) = self._letterbox(frame, (self.img_size, self.img_size))
            
            # Convert RGB (Picamera standard) to BGR (OpenCV standard) for display/inference compatibility
            # Note: Depending on training, you might need RGB. 
            # But usually cv2 functions expect BGR for saving/showing.
            # Here we convert for inference input preparation.
            img_input = cv2.cvtColor(img, cv2.COLOR_RGB2BGR).astype(np.float32)/255.0
            img_input = np.transpose(img_input, (2,0,1))[None,...]

            # 4. Inference
            out = self.session.run([self.output_name], {self.input_name: img_input})[0]
            
            # 5. Post-processing
            preds = np.squeeze(out, 0).T
            boxes = preds[:, :4]
            scores = preds[:, 4:]
            conf_max = scores.max(1)
            mask = conf_max > self.conf_thres
            
            boxes = boxes[mask]
            conf_max = conf_max[mask]

            found = False
            cx, cy = 0.5, 0.5

            if len(boxes) > 0:
                best_idx = np.argmax(conf_max)
                bx, by, bw, bh = boxes[best_idx]
                
                cx = bx/self.img_size
                cy = by/self.img_size
                found = True
                
                # Draw Box
                x1 = int((bx - bw/2 - dw)/ratio)
                y1 = int((by - bh/2 - dh)/ratio)
                x2 = int((bx + bw/2 - dw)/ratio)
                y2 = int((by + bh/2 - dh)/ratio)
                
                # Draw on 'frame' (which is RGB from Picamera)
                # OpenCV imshow expects BGR, so colors might look swapped (Blue<->Red)
                # unless we convert frame to BGR for display.
                # Let's convert frame to BGR for correct display colors.
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), (0,0,255), 3)
                cv2.putText(frame_bgr, f"FIRE: {conf_max[best_idx]:.2f}", (x1,y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
                
                # Update frame reference for display
                frame = frame_bgr
            else:
                # Even if no detection, convert to BGR for natural colors
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # 6. Show Window
            cv2.imshow("Robot Vision", frame)
            cv2.waitKey(1)
            
            return found, cx, cy

        except Exception as e:
            print(f"[Camera] Processing Error: {e}")
            return False, 0.5, 0.5

    def cleanup(self):
        if self.picam2:
            self.picam2.stop()
            self.picam2.close() # Ensure resource release
        cv2.destroyAllWindows()
        print("[Camera] Picamera2 resources released.")
