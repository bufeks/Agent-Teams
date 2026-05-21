# Agent Teams — Creative Agency AI Framework

Claude APIを使ったマルチエージェントのクリエイティブエージェンシーチームです。ECDがオーケストレーターとして、複数の専門エージェントを指揮してキャンペーン開発を行います。複数案件を独立して走らせることを前提に設計されています。

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

## ディレクトリ構成

```
Agent-Teams/
├── agent_team.py        # エージェントチーム本体（フレームワーク）
├── knowledge_base.py    # ナレッジ読み込み（ファイル + Bear）
├── bear_notes.py        # Bear メモ連携
├── main.py              # 汎用実行スクリプト
├── knowledge/           # 全案件共通のナレッジ（PDF・PPT・MD等）
└── output/              # 実行結果（ローカルのみ・git管理外）
```

案件固有のスクリプトや資料はこのリポジトリには含めず、別途管理してください。

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
```

## 使い方

**ブリーフを直接渡す（推奨）:**

```bash
python main.py "ここにブリーフを書く"
```

**デモブリーフで実行:**

```bash
python main.py
```

**Bear メモをナレッジに含める（コードから）:**

```python
import knowledge_base
kb = knowledge_base.load(bear_tags=["campaign"], bear_query="キーワード")
```

## ナレッジベース

`knowledge/` フォルダに PDF・PPT・TXT・MD を置くと全エージェントの前提知識になります。案件をまたいで共通で参照したい資料（クレデンシャル、参考事例等）を置いてください。

## 出力について

エージェントの出力はターミナルに表示されます。ファイル保存が必要な場合はリダイレクトで対応してください：

```bash
python main.py "ブリーフ" > output/result.md
```

`output/` は `.gitignore` 済みのため、結果がリポジトリに混入しません。

## 依存関係

- `anthropic` — Claude API（claude-opus-4-7使用）
- `python-dotenv` — 環境変数管理
- `pymupdf` — PDF読み込み
- `python-pptx` — PowerPoint読み込み
