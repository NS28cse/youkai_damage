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
- ログイン: 既定の `oauth2` 方式では、表示された URL をブラウザで開いてログインし、表示されたコードを端末に貼り付ける。ブラウザのない環境でも使える。トークンは `~/.config/colab-cli/token.json` に保存される。
- GPU 利用は Colab の利用枠（無料枠・コンピューティングユニット）を消費する。無料プランで CLI がどこまで使えるかは未確認。

### Claude Code のクラウドセッションから使う場合（2026-10-29 確認）

- インストールと、Colab・Google ログインの各サーバーへの接続は確認済み。
- ログインはオーナー本人の操作が必要（Q6）。

## Claude Code のクラウドセッションのネットワーク設定

Gemini の共有リンクを読むには、環境のネットワーク設定で次のドメインの許可が必要だった。

- `share.gemini.google`（共有リンク）
- `gemini.google.com`（転送先）

共有ページ自体は JavaScript で描画され、その JavaScript は `gstatic.com` から配信される（未許可）。そのため、ページは描画せずに `gemini.google.com` の会話データ取得用の内部エンドポイントから直接取得した。
