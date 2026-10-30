"""実現性検証用の合成データ生成。

3DS 上画面 (400x240) を模した画像にオレンジ(ダメージ)/緑(回復)の数字を描き、
スマホカメラで画面を撮った状態 (LCD の画素格子、斜め、ぼけ、色ずれ、ノイズ、JPEG) を再現する。
実際のゲーム画面・フォントではない点に注意 (結果の解釈は README.md を参照)。

出力:
  det/images/{split}/*.jpg, det/labels/{split}/*.txt  数字列の検出 (0=damage, 1=heal)
  ocr/images/{split}/*.jpg, ocr/labels/{split}/*.txt  数字列の切り抜きと各桁の位置 (0-9)
  gt_{split}.json                                      評価用の正解 (枠・種類・値・数字の高さ)
"""
import argparse
import json
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

NW, NH = 400, 240    # 3DS 上画面
FW, FH = 1280, 720   # カメラ映像 (720p)
UP = 4               # LCD 格子を描くための拡大率
COLORS = {0: (255, 145, 30), 1: (90, 230, 70)}  # 0=damage(オレンジ), 1=heal(緑)


def jitter(c, rng, d=25):
    return tuple(int(np.clip(v + rng.integers(-d, d + 1), 0, 255)) for v in c)


def background(rng, font_path):
    t = np.linspace(0, 1, NH)[:, None, None]
    img = (rng.uniform(0, 255, 3) * (1 - t) + rng.uniform(0, 255, 3) * t) * np.ones((NH, NW, 3))
    pil = Image.fromarray(img.astype(np.uint8))
    d = ImageDraw.Draw(pil)
    for _ in range(rng.integers(5, 25)):
        x, y = int(rng.integers(-50, NW)), int(rng.integers(-50, NH))
        box = [x, y, x + int(rng.integers(10, 150)), y + int(rng.integers(10, 120))]
        col = tuple(int(v) for v in rng.uniform(0, 255, 3))
        (d.ellipse if rng.random() < 0.5 else d.rectangle)(box, fill=col)
    # 紛らわしいもの: オレンジ/緑のエフェクト、白や黄色の無関係な数字
    for _ in range(rng.integers(0, 4)):
        x, y, r = int(rng.integers(0, NW)), int(rng.integers(0, NH)), int(rng.integers(5, 40))
        d.ellipse([x - r, y - r, x + r, y + r], fill=jitter(COLORS[int(rng.integers(0, 2))], rng, 40))
    for _ in range(rng.integers(0, 3)):
        f = ImageFont.truetype(font_path, int(rng.integers(8, 14)))
        d.text((int(rng.integers(0, NW - 40)), int(rng.integers(0, NH - 15))), str(int(rng.integers(0, 999))),
               font=f, fill=jitter((240, 240, 200), rng))
    return pil


def draw_number(img, rng, font_path, taken):
    """数字列を1つ描く。重なる場合は None。"""
    cls = int(rng.integers(0, 2))
    value = str(int(np.exp(rng.uniform(0, np.log(10000)))))
    h = int(rng.integers(8, 15))  # 数字の高さ (ネイティブ画素)
    font = ImageFont.truetype(font_path, int(round(h / 0.73)))  # 数字の高さ ≒ 0.73 × フォントサイズ
    stroke = 1
    width = font.getlength(value) + 2 * stroke
    x0, y0 = rng.uniform(2, NW - width - 2), rng.uniform(2, NH - h / 0.73 - 4)
    layer = Image.new("RGBA", (NW, NH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    outline = (30, 20, 10) if rng.random() < 0.7 else (250, 250, 250)
    digits, x = [], x0
    for ch in value:
        d.text((x, y0), ch, font=font, fill=jitter(COLORS[cls], rng), stroke_width=stroke, stroke_fill=outline)
        digits.append((int(ch), d.textbbox((x, y0), ch, font=font, stroke_width=stroke)))
        x += font.getlength(ch)
    box = (min(b[0] for _, b in digits), min(b[1] for _, b in digits),
           max(b[2] for _, b in digits), max(b[3] for _, b in digits))
    if any(not (box[2] < t[0] or t[2] < box[0] or box[3] < t[1] or t[3] < box[1]) for t in taken):
        return None
    alpha = rng.uniform(0.5, 1.0)  # 出現・消滅中の半透明
    layer.putalpha(Image.fromarray((np.array(layer)[..., 3] * alpha).astype(np.uint8)))
    img.alpha_composite(layer)
    return {"cls": cls, "value": value, "h": h, "box": box, "digits": digits}


def camera(native, rng):
    """ネイティブ画面 → カメラ映像。返り値: (画像, 座標変換行列)"""
    up = cv2.resize(native, (NW * UP, NH * UP), interpolation=cv2.INTER_NEAREST).astype(np.float32)
    g = rng.uniform(0.6, 0.9)
    up[UP - 1::UP, :] *= g
    up[:, UP - 1::UP] *= g
    sh = rng.uniform(0.80, 0.98) * FH
    sw = sh * NW / NH
    cx, cy = FW / 2 + rng.uniform(-60, 60), FH / 2 + rng.uniform(-0.01, 0.01) * FH
    dst = np.float32([[cx - sw / 2, cy - sh / 2], [cx + sw / 2, cy - sh / 2],
                      [cx + sw / 2, cy + sh / 2], [cx - sw / 2, cy + sh / 2]])
    dst += rng.uniform(-0.02, 0.02, (4, 2)).astype(np.float32) * np.float32([sw, sh])
    src = np.float32([[0, 0], [NW * UP, 0], [NW * UP, NH * UP], [0, NH * UP]])
    H = cv2.getPerspectiveTransform(src, dst)
    bezel = float(rng.uniform(15, 45))
    frame = cv2.warpPerspective(up, H, (FW, FH), flags=cv2.INTER_LINEAR, borderValue=(bezel,) * 3)
    k = rng.uniform(0.3, 1.5)
    frame = cv2.GaussianBlur(frame, (0, 0), k)
    if rng.random() < 0.2:  # 手ぶれ
        n = int(rng.integers(3, 8))
        ker = np.zeros((n, n), np.float32)
        ker[n // 2] = 1 / n
        M = cv2.getRotationMatrix2D((n / 2, n / 2), rng.uniform(0, 180), 1)
        frame = cv2.filter2D(frame, -1, cv2.warpAffine(ker, M, (n, n)))
    frame = frame * rng.uniform(0.9, 1.1, 3) * rng.uniform(0.7, 1.2)
    frame = 255 * (np.clip(frame, 0, 255) / 255) ** rng.uniform(0.8, 1.25)
    if rng.random() < 0.3:  # 映り込み
        yy, xx = np.mgrid[0:FH, 0:FW]
        gx, gy, r = rng.uniform(0, FW), rng.uniform(0, FH), rng.uniform(100, 400)
        frame += rng.uniform(10, 40) * np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * r * r))[..., None]
    frame += rng.normal(0, rng.uniform(1, 6), frame.shape)
    frame = np.clip(frame, 0, 255).astype(np.uint8)
    ok, enc = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(60, 93))])
    return cv2.imdecode(enc, cv2.IMREAD_COLOR), H


def map_box(b, H):
    pts = np.float32([[b[0], b[1]], [b[2], b[1]], [b[2], b[3]], [b[0], b[3]]]) * UP
    p = cv2.perspectiveTransform(pts[None], H)[0]
    return [float(p[:, 0].min()), float(p[:, 1].min()), float(p[:, 0].max()), float(p[:, 1].max())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--font", default="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    ap.add_argument("--splits", default="train:3000,val:400,test:400")
    args = ap.parse_args()
    for si, spec in enumerate(args.splits.split(",")):
        split, n = spec.split(":")
        rng = np.random.default_rng(1000 + si)
        for sub in ("det/images", "det/labels", "ocr/images", "ocr/labels"):
            os.makedirs(f"{args.out}/{sub}/{split}", exist_ok=True)
        gt = {}
        for i in range(int(n)):
            img = background(rng, args.font).convert("RGBA")
            nums, taken = [], []
            for _ in range(int(rng.integers(0, 5))):  # 0 個 (数字なし) も含める
                r = draw_number(img, rng, args.font, taken)
                if r:
                    nums.append(r)
                    taken.append(r["box"])
            native = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
            frame, H = camera(native, rng)
            name = f"{split}_{i:05d}"
            cv2.imwrite(f"{args.out}/det/images/{split}/{name}.jpg", frame)
            lines, recs = [], []
            for j, r in enumerate(nums):
                x0, y0, x1, y1 = map_box(r["box"], H)
                lines.append(f"{r['cls']} {(x0 + x1) / 2 / FW:.6f} {(y0 + y1) / 2 / FH:.6f} "
                             f"{(x1 - x0) / FW:.6f} {(y1 - y0) / FH:.6f}")
                recs.append({"cls": r["cls"], "value": r["value"], "h": r["h"], "box": [x0, y0, x1, y1]})
                # 文字認識用: 検出枠のずれを模して余白をランダムに付けて切り抜く
                bw, bh = x1 - x0, y1 - y0
                pad = rng.uniform(0.05, 0.25, 4) * np.array([bw, bh, bw, bh])
                cx0, cy0 = max(0, int(x0 - pad[0])), max(0, int(y0 - pad[1]))
                cx1, cy1 = min(FW, int(x1 + pad[2])), min(FH, int(y1 + pad[3]))
                crop = frame[cy0:cy1, cx0:cx1]
                cw, ch = cx1 - cx0, cy1 - cy0
                dl = []
                for dgt, db in r["digits"]:
                    a0, b0, a1, b1 = map_box(db, H)
                    a0, a1 = np.clip([a0 - cx0, a1 - cx0], 0, cw)
                    b0, b1 = np.clip([b0 - cy0, b1 - cy0], 0, ch)
                    dl.append(f"{dgt} {(a0 + a1) / 2 / cw:.6f} {(b0 + b1) / 2 / ch:.6f} "
                              f"{(a1 - a0) / cw:.6f} {(b1 - b0) / ch:.6f}")
                cv2.imwrite(f"{args.out}/ocr/images/{split}/{name}_{j}.jpg", crop)
                with open(f"{args.out}/ocr/labels/{split}/{name}_{j}.txt", "w") as f:
                    f.write("\n".join(dl) + "\n")
            with open(f"{args.out}/det/labels/{split}/{name}.txt", "w") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
            gt[name] = recs
        with open(f"{args.out}/gt_{split}.json", "w") as f:
            json.dump(gt, f)
        print(split, n, "images,", sum(len(v) for v in gt.values()), "numbers")


if __name__ == "__main__":
    main()
