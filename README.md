# youkai_damage

ニンテンドー3DS の「妖怪ウォッチ」（初代・2）の上画面に表示されるダメージ・回復の数値を、Android スマホのカメラでリアルタイムに認識して記録し、Webページ上の表に表示して CSV でダウンロードできるようにするプロジェクト。

> **現在の段階: 設計・データ収集計画、合成データでの実現性検証中**（2026-10-30 時点）。検証用コードは [experiments/feasibility/](experiments/feasibility/)。

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
| [experiments/feasibility/](experiments/feasibility/README.md) | 合成データでの実現性検証（方法・結果） |
| [CONTRIBUTING.md](CONTRIBUTING.md) | **記録のルール**（参加する人は必読） |
