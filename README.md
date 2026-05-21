# Agent Teams — Creative Agency AI Framework

Claude APIを使ったマルチエージェントのクリエイティブエージェンシーチームです。ECDがオーケストレーターとして、複数の専門エージェントを指揮してキャンペーン開発を行います。

## エージェント構成

```
ECD（オーケストレーター）
├── Researcher
├── Strategic Planner
└── CD（サブオーケストレーター）
    ├── Challenger（コンセプトの検証・再構築）
    ├── Activation Planner
    ├── CopyWriter
    └── Art Director
```

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
```

## 使い方

デモブリーフを実行（デフォルトは1件目）:

```bash
python main.py
```

カスタムブリーフを渡す:

```bash
python main.py "ここにブリーフを書く"
```

## ナレッジベース

`knowledge/` フォルダにPDF・PPT・TXTを置くと、全エージェントの前提知識として参照されます。

## 依存関係

- `anthropic` — Claude API（claude-opus-4-7使用）
- `python-dotenv` — 環境変数管理
- `pymupdf` — PDF読み込み
- `python-pptx` — PowerPoint読み込み
