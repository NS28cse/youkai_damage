"""合成データで 検出(YOLO) → 文字認識(YOLO で各桁を検出) を学習し、通しで評価する。Colab の GPU で実行する想定。

使い方: python train_eval.py <gen_synth.py の出力先> <結果の出力先>
"""
import json
import os
import sys
import time

import cv2
from ultralytics import YOLO

data, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
EPOCHS = int(os.environ.get("EPOCHS", "30"))


def yaml(path, root, names):
    with open(path, "w") as f:
        f.write(f"path: {root}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n")
        f.writelines(f"  {i}: '{n}'\n" for i, n in enumerate(names))


yaml(f"{out}/det.yaml", f"{data}/det", ["damage", "heal"])
yaml(f"{out}/ocr.yaml", f"{data}/ocr", [str(i) for i in range(10)])
# 左右反転は数字の形を壊すので使わない
common = dict(epochs=EPOCHS, fliplr=0.0, project=out, exist_ok=True, verbose=False, plots=False)

t = time.time()
YOLO("yolo11n.pt").train(data=f"{out}/det.yaml", imgsz=640, batch=32, name="det", **common)
YOLO("yolo11n.pt").train(data=f"{out}/ocr.yaml", imgsz=192, batch=64, mosaic=0.0, name="ocr", **common)
train_min = (time.time() - t) / 60

det = YOLO(f"{out}/det/weights/best.pt")
ocr = YOLO(f"{out}/ocr/weights/best.pt")
m = det.val(data=f"{out}/det.yaml", split="test", imgsz=640, verbose=False, plots=False)
det_metrics = {"mAP50": float(m.box.map50), "mAP50_95": float(m.box.map),
               "mAP50_per_class": {n: float(v) for n, v in zip(["damage", "heal"], m.box.ap50)}}


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-9)


def read_number(img, box):
    x0, y0, x1, y1 = box
    px, py = 0.1 * (x1 - x0), 0.1 * (y1 - y0)
    crop = img[max(0, int(y0 - py)):int(y1 + py), max(0, int(x0 - px)):int(x1 + px)]
    if crop.size == 0:
        return ""
    r = ocr(crop, imgsz=192, conf=0.25, agnostic_nms=True, verbose=False)[0].boxes
    return "".join(str(int(c)) for _, c in sorted(zip(r.xyxy[:, 0].tolist(), r.cls.tolist())))


# 通し評価: 位置(IoU>=0.5)・種類・値がすべて合って正解
gt = json.load(open(f"{data}/gt_test.json"))
bins = {"h8-9": (8, 9), "h10-11": (10, 11), "h12-14": (12, 14)}
stat = {k: dict(gt=0, found=0, cls_ok=0, val_ok=0, all_ok=0) for k in bins}
fp = n_pred = 0
t = time.time()
for name, recs in gt.items():
    img = cv2.imread(f"{data}/det/images/test/{name}.jpg")
    p = det(img, imgsz=640, conf=0.25, verbose=False)[0].boxes
    preds = [(b, int(c), read_number(img, b)) for b, c in zip(p.xyxy.tolist(), p.cls.tolist())]
    n_pred += len(preds)
    used = set()
    for r in recs:
        k = next(k for k, (lo, hi) in bins.items() if lo <= r["h"] <= hi)
        stat[k]["gt"] += 1
        best = max(((iou(b, r["box"]), i) for i, (b, _, _) in enumerate(preds) if i not in used), default=(0, -1))
        if best[0] < 0.5:
            continue
        used.add(best[1])
        _, c, v = preds[best[1]]
        s = stat[k]
        s["found"] += 1
        s["cls_ok"] += c == r["cls"]
        s["val_ok"] += v == r["value"]
        s["all_ok"] += c == r["cls"] and v == r["value"]
    fp += len(preds) - len(used)
ms = (time.time() - t) / len(gt) * 1000

tot = {f: sum(s[f] for s in stat.values()) for f in ["gt", "found", "cls_ok", "val_ok", "all_ok"]}
res = {"epochs": EPOCHS, "train_minutes": round(train_min, 1), "det_test": det_metrics,
       "e2e_total": tot, "e2e_by_digit_height": stat, "false_positives": fp, "predictions": n_pred,
       "e2e_recall_all_correct": tot["all_ok"] / tot["gt"], "e2e_precision_all_correct": tot["all_ok"] / max(1, n_pred),
       "pipeline_ms_per_frame_gpu": round(ms, 1)}
json.dump(res, open(f"{out}/results.json", "w"), indent=2)
print(json.dumps(res, indent=2))

for model, size, tag in [(det, 640, "det"), (det, 320, "det"), (ocr, 192, "ocr")]:
    os.replace(model.export(format="onnx", imgsz=size, opset=12), f"{out}/{tag}_{size}.onnx")
