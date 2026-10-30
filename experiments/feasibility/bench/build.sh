#!/usr/bin/env bash
# 速度テストページの配布物を組み立てる。
# 使い方: bench/build.sh <ONNX モデルのあるディレクトリ> <出力先>
#   モデルは train_eval.py が出力する det_640.onnx, det_320.onnx, ocr_192.onnx
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
models="$1"; out="$2"
ORT_VERSION=1.30.0
mkdir -p "$out"
tmp="$(mktemp -d)"
(cd "$tmp" && npm pack -s "onnxruntime-web@$ORT_VERSION" >/dev/null && tar xzf "onnxruntime-web-$ORT_VERSION.tgz")
cp "$tmp/package/dist/ort.wasm.bundle.min.mjs" "$tmp/package/dist/ort-wasm-simd-threaded.wasm" "$out/"
cp "$models"/det_640.onnx "$models"/det_320.onnx "$models"/ocr_192.onnx "$out/"
cp "$here/index.html" "$out/"
# サンプル画像: 学習に使わない test 分割の先頭3枚と同じ生成条件
python3 "$here/../gen_synth.py" --out "$tmp/synth" --splits train:0,val:0,test:3
for i in 0 1 2; do cp "$tmp/synth/det/images/test/test_0000$i.jpg" "$out/sample_$i.jpg"; done
rm -rf "$tmp"
ls -la "$out"
