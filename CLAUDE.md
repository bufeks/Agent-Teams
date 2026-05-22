# CLAUDE.md

## このリポジトリの使い方

クリエイティブエージェンシーのAIチームを動かすフレームワーク。
ブリーフを渡すと、ECD・Researcher・Strategic Planner・CD・CW・AD・Activation Planner・Challenger が協働してキャンペーンを開発し、HTMLで出力する。

### 運用の基本

- **案件ごとにセッションを分ける**。案件固有のファイルはセッション内だけで扱い、リポジトリには残さない
- `output/` と `briefings/` `clients/` は `.gitignore` 済み。git に案件ファイルが混入しない

### ブリーフを渡されたら

ユーザーがブリーフ（テキスト・ファイル）を渡してきたら、確認せずそのまま以下を実行する：

**テキストブリーフの場合：**
```bash
python main.py "受け取ったブリーフをそのまま入れる"
```

**オリエン資料ファイル（PDF/PPT/TXT）の場合：**
ユーザーがファイルをアップロードすると `/root/.claude/uploads/...` に置かれる。そのパスをそのまま使う：
```bash
python main.py --file /root/.claude/uploads/<hash>/<filename>.pdf
python main.py --file /root/.claude/uploads/<hash>/<filename>.pdf "追加指示があればここに"
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

### 発見・知見をリポジトリに蓄積する

セッション中に以下のような「普遍化できる発見」が生まれたら、クライアント名・固有情報を除いてリポジトリに残す：

- クリエイティブの原則・法則・構造的パターン
- 「なぜこれが機能したか」の構造的な分析
- 広告・マーケティング・チームデザインに関する新しい視点
- AIチームを動かして見えてきた仕事の本質

**書き先：**
- `knowledge/宮崎太郎のクリエイティブ論/発見ログ/YYYY.md` — 時系列の発見メモ
- `knowledge/宮崎太郎のクリエイティブ論/原則/` — 再現可能な原則として独立させる価値があるもの
- `knowledge/宮崎太郎のクリエイティブ論/_overview.md` — 理論の全体像が更新されるとき

**判断基準：**
「このブリーフがなくても成立する話か？」→ YESなら残す価値がある。

commit して push する。

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
