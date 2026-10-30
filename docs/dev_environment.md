# 開発環境・ツール

最終更新: 2026-10-29

## 方針（決定 D8）

| 工程 | ツール |
|---|---|
| モデルの学習・実験 | Google Colaboratory（GPU） |
| アプリ開発 | PyCharm Professional（学生向け無料） |

大きなデータ（動画・画像・学習済みモデル）は Google Drive に置き、git には入れない。

## Google Colab CLI

Google 公式の Colab のコマンドラインツール（2026年6月公開）。ターミナルや AI エージェントから Colab の GPU 実行環境を使える。

- リポジトリ: https://github.com/googlecolab/google-colab-cli
- 対応 OS: Linux / macOS のみ（Windows は非対応）
- インストール:

```bash
uv tool install google-colab-cli
```

- 主なコマンド:
  - `colab new --gpu T4` … GPU の実行環境を作る
  - `colab exec` … スクリプトや `.ipynb` を実行する
  - `colab download` … 実行環境からファイルを取り出す
  - `colab stop` … 実行環境を止める
  - `colab run` … 作成 → 実行 → 結果回収 → 停止を1回で行う
- 認証は2通り:
  - `oauth2`（既定）: 表示された URL をブラウザで開いてログインし、表示されたコードを端末に貼り付ける。トークンは `~/.config/colab-cli/token.json` に保存される。
  - `adc`: Application Default Credentials の JSON を使う。ファイルの場所を `GOOGLE_APPLICATION_CREDENTIALS` で指定し、`colab --auth adc ...` で実行する。
- GPU 利用は Colab のコンピューティングユニットを消費する。残高は `colab usage` で確認できる。

### クラウド・自動化環境での認証（2026-10-30 確認済み）

オーナーの ADC JSON を base64 にしたものを環境変数 `COLAB_ADC_B64` に設定してある。中身は絶対にコミットしない。

```bash
umask 077; mkdir -p ~/.config/colab-cli
echo "$COLAB_ADC_B64" | base64 -d > ~/.config/colab-cli/adc.json
export GOOGLE_APPLICATION_CREDENTIALS=~/.config/colab-cli/adc.json
colab --auth adc usage
```

## 外部リンクの取得に必要なネットワーク許可

ネットワークが制限された環境で Gemini の共有リンクを読むには `share.gemini.google` と `gemini.google.com` の許可が必要。共有ページは `gstatic.com` から配信される JavaScript で描画されるため、それを許可しない場合はページを描画できない。
