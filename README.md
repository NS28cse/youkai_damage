# youkai_damage

ゲーム画面に表示されるダメージ・回復の数値を、スマホカメラでリアルタイムに認識して記録し、Webページ上の表に表示して CSV でダウンロードできるようにするプロジェクト。

> **現在の段階: 設計・データ収集計画**（2026-10-29 時点）。コードはまだありません。

## ドキュメント

新しく参加する人は、上から順に読んでください。

| ファイル | 内容 |
|---|---|
| [docs/overview.md](docs/overview.md) | 目的・要件・システム構成（現時点の案） |
| [docs/decisions.md](docs/decisions.md) | 決定事項と提案の記録（**決定済み / 提案中 / 取り下げ** を区別） |
| [docs/open_questions.md](docs/open_questions.md) | 未解決の質問・確認待ちの事項 |
| [docs/data_collection_plan.md](docs/data_collection_plan.md) | 学習・評価データの収集計画 |
| [docs/background.md](docs/background.md) | ここまでの経緯（Gemini での検討と、その計画のレビュー） |
| [docs/dev_environment.md](docs/dev_environment.md) | 開発環境・ツール（Colab, Colab CLI など） |

## 記録のルール

他の人が途中から開発に加わることを前提に、判断の経緯を必ず残します。

- 何かを決めたら [docs/decisions.md](docs/decisions.md) に追記する（日付・決めた人・理由・状態）。
- 疑問や未確定事項は [docs/open_questions.md](docs/open_questions.md) に書き、解決したら決定事項へ移す。
- 計画や構成が変わったら、該当ドキュメントを同じコミットで更新する。
- 大きなデータ（動画・画像・学習済みモデル）は git に入れない（Google Drive などに置き、場所をドキュメントに書く）。
