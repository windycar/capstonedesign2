# detector.py
import os
import time
import numpy as np
import cv2
import onnxruntime as ort

def letterbox(im, new_shape, color=(114, 114, 114)):
    """Resize and pad image to new_shape."""
    h, w = im.shape[:2]
    r = min(new_shape[0] / h, new_shape[1] / w)
    nh, nw = int(round(h * r)), int(round(w * r))
    resized = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((new_shape[0], new_shape[1], 3), color, dtype=np.uint8)
    top = (new_shape[0] - nh) // 2
    left = (new_shape[1] - nw) // 2
    canvas[top:top + nh, left:left + nw] = resized
    return canvas, r, (left, top)

def nms_np(boxes_xyxy, scores, iou_thr=0.45):
    """Perform Non-Maximum Suppression (NMS) on numpy arrays."""
    if len(boxes_xyxy) == 0:
        return []
    boxes = boxes_xyxy.astype(np.float32)
    order = np.asarray(scores).argsort()[::-1]
    keep = []
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    while order.size > 0:
        i = order[0]
        keep.append(i)
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(iou <= iou_thr)[0]
        order = order[inds + 1]
    return keep

class Detector:
    """ONNX Runtime Detector Class for YOLO model."""
    def __init__(self, model_path="best.onnx", img_size=320, iou_thr=0.45, conf_off=0.40, ort_threads=4, labels=["fire"]):
        print(f"[INFO] Loading ONNX model: {model_path}")
        self.img_size = img_size
        self.iou_thr = iou_thr
        self.conf_off = conf_off
        self.labels = labels

        so = ort.SessionOptions()
        so.intra_op_num_threads = ort_threads
        os.environ.setdefault("OMP_NUM_THREADS", str(ort_threads))
        os.environ.setdefault("OPENBLAS_NUM_THREADS", str(ort_threads))

        self.session = ort.InferenceSession(
            model_path, sess_options=so, providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        print(f"[INFO] Detector initialized.")

    def infer(self, frame):
        """Run inference on a single frame."""
        h0, w0 = frame.shape[:2]
        lb, r, (padx, pady) = letterbox(frame, (self.img_size, self.img_size))
        img = cv2.cvtColor(lb, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))[None, ...]

        t0 = time.time()
        out0 = self.session.run([self.output_name], {self.input_name: img})[0]
        infer_ms = (time.time() - t0) * 1000.0

        preds = np.squeeze(out0, 0).T
        boxes = preds[:, :4]
        probs = preds[:, 4:]
        cids = probs.argmax(1)
        confs = probs.max(1)

        m = confs > self.conf_off
        boxes, confs, cids = boxes[m], confs[m], cids[m]

        boxes_xyxy = np.empty((0, 4), dtype=np.float32)
        
        if len(boxes) > 0:
            cx, cy, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
            x1 = (cx - w / 2 - padx) / r
            y1 = (cy - h / 2 - pady) / r
            x2 = (cx + w / 2 - padx) / r
            y2 = (cy + h / 2 - pady) / r

            x1 = np.clip(x1, 0, w0 - 1)
            y1 = np.clip(y1, 0, h0 - 1)
            x2 = np.clip(x2, 0, w0 - 1)
            y2 = np.clip(y2, 0, h0 - 1)

            boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)
            keep = nms_np(boxes_xyxy, confs, self.iou_thr)
            boxes_xyxy = boxes_xyxy[keep]
            confs = confs[keep]
            cids = cids[keep]

        return boxes_xyxy, confs, cids, infer_ms

    def draw_detections(self, frame, boxes_xyxy, confs, cids):
        """Draw detections on the frame."""
        fire_now = False
        for (x1, y1, x2, y2), conf, cid in zip(boxes_xyxy, confs, cids):
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            
            name = self.labels[cid] if cid < len(self.labels) else str(cid)
            text = f"{name}:{conf:.2f}"
            
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 6, y1 + 4), (0, 0, 0), -1)
            cv2.putText(frame, text, (x1 + 3, y1 - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            fire_now = True # Assuming any detection is fire
        return frame, fire_now