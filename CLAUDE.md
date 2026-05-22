# CLAUDE.md

## このリポジトリの使い方

クリエイティブエージェンシーのAIチームを動かすフレームワーク。
ブリーフを渡すと、ECD・Researcher・Strategic Planner・CD・CW・AD・Activation Planner・Challenger が協働してキャンペーンを開発し、HTMLで出力する。

### ブリーフを渡されたら

ユーザーがブリーフ（キャンペーン依頼・案件概要）を渡してきたら、確認せずそのまま以下を実行する：

```bash
python main.py "受け取ったブリーフをそのまま入れる"
```

出力は `output/` にHTMLで自動保存される。完了したらファイルパスをユーザーに伝える。

### Bear メモを使いたい場合

ユーザーが「Bearの〇〇タグを使って」「〇〇で検索して」と言ったら、`main.py` を直接書き換えず、以下のようにワンライナーで対応する：

```bash
python -c "
import os; from dotenv import load_dotenv; load_dotenv()
from agent_team import CreativeTeam
import knowledge_base
team = CreativeTeam()
team.knowledge = knowledge_base.load(bear_tags=['タグ名'], bear_query='キーワード')
result = team.run('ブリーフ')
from pathlib import Path; from datetime import datetime
p = Path('output') / f'{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.html'
p.parent.mkdir(exist_ok=True); p.write_text(result.to_html(), encoding='utf-8')
print(p)
"
```

---

## TODO

### AIに任せていいもの（ものづくりにおける「捨ててもいい時間」の整理）

- 情報収集
- 競合整理
- 論点整理
- 既存表現のパターン出し
- 初期コピー案
- 構成案
- 打ち合わせメモの要約
- ブリーフの複数解釈
- 企画の穴探し
- 表現の言い換え
- 資料のたたき台

これらは、ものづくりにおいて「捨ててもいい時間」になりうる。
少なくとも、人間が毎回ゼロから手で抱え込む必要はない。
