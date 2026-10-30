"""書き出した ONNX モデルで通し評価する（ブラウザと同じ前処理・後処理）。入力サイズ別の精度比較用。

使い方: python eval_onnx.py <gen_synth.py の出力先> <det の onnx> <ocr の onnx>
"""
import json
import sys
from collections import defaultdict

import cv2
import numpy as np
import onnxruntime as ort

data, det_path, ocr_path = sys.argv[1:4]
det = ort.InferenceSession(det_path, providers=["CPUExecutionProvider"])
ocr = ort.InferenceSession(ocr_path, providers=["CPUExecutionProvider"])


def letterbox(img, size):
    h, w = img.shape[:2]
    r = min(size / w, size / h)
    nw, nh = round(w * r), round(h * r)
    px, py = (size - nw) / 2, (size - nh) / 2
    canvas = np.full((size, size, 3), 114, np.uint8)
    canvas[int(py):int(py) + nh, int(px):int(px) + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    x = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)[None].astype(np.float32) / 255
    return x, r, int(px), int(py)


def run(sess, img, conf=0.25, iou_th=0.5):
    size = sess.get_inputs()[0].shape[2]
    x, r, px, py = letterbox(img, size)
    out = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]  # [4+nc, N]
    scores = out[4:]
    cls, best = scores.argmax(0), scores.max(0)
    keep = best >= conf
    cx, cy, w, h = out[:4, keep]
    boxes = np.stack([(cx - w / 2 - px) / r, (cy - h / 2 - py) / r, (cx + w / 2 - px) / r, (cy + h / 2 - py) / r], 1)
    order = np.argsort(-best[keep])
    res = []
    for i in order:
        if all(iou(boxes[i], b) < iou_th for b, _ in res):
            res.append((boxes[i], int(cls[keep][i])))
    return res


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-9)


def read_number(img, b):
    px, py = 0.1 * (b[2] - b[0]), 0.1 * (b[3] - b[1])
    crop = img[max(0, int(b[1] - py)):int(b[3] + py), max(0, int(b[0] - px)):int(b[2] + px)]
    if crop.size == 0:
        return ""
    return "".join(str(c) for d, c in sorted(run(ocr, crop), key=lambda t: t[0][0]))


gt = json.load(open(f"{data}/gt_test.json"))
stat = defaultdict(lambda: defaultdict(int))
n_pred = matched = 0
for name, recs in gt.items():
    img = cv2.imread(f"{data}/det/images/test/{name}.jpg")
    preds = [(b, c, read_number(img, b)) for b, c in run(det, img)]
    n_pred += len(preds)
    used = set()
    for r in recs:
        k = "h8-9" if r["h"] <= 9 else "h10-11" if r["h"] <= 11 else "h12-14"
        stat[k]["gt"] += 1
        cand = [(iou(b, r["box"]), i) for i, (b, _, _) in enumerate(preds) if i not in used]
        best = max(cand, default=(0, -1))
        if best[0] < 0.5:
            continue
        used.add(best[1])
        _, c, v = preds[best[1]]
        stat[k]["all_ok"] += c == r["cls"] and v == r["value"]
    matched += len(used)
tot_gt = sum(s["gt"] for s in stat.values())
tot_ok = sum(s["all_ok"] for s in stat.values())
print(json.dumps({"det": det_path.split("/")[-1], "recall_all_correct": round(tot_ok / tot_gt, 4),
                  "precision_all_correct": round(tot_ok / max(1, n_pred), 4),
                  "by_height": {k: f'{v["all_ok"]}/{v["gt"]}' for k, v in sorted(stat.items())}}, ensure_ascii=False))
