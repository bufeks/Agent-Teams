# CLAUDE.md

## このリポジトリの使い方

クリエイティブエージェンシーのAIチームを動かすフレームワーク。
ブリーフを渡すと、ECD・Researcher・Strategic Planner・CD・CW・AD・Activation Planner・Challenger が協働してキャンペーンを開発し、HTMLで出力する。

**実行方式：Claude Code（このチャット）が直接エージェントチームとして動く。外部APIは使わない。MAXプラン内で完結する。**

### 運用の基本

- **案件ごとにセッションを分ける**。案件固有のファイルはセッション内だけで扱い、リポジトリには残さない
- `output/` と `briefings/` `clients/` は `.gitignore` 済み。git に案件ファイルが混入しない

---

### ブリーフを渡されたら

ユーザーがブリーフ（テキスト・ファイル）を渡してきたら、**確認せず**そのまま以下のフローを実行する。

**⚠️ `python main.py` は絶対に実行しない。** APIキーが不要なエージェントチーム実行フローを直接使う。

**ファイル（PDF/PPT/TXT）の場合：**
アップロードファイルは `/root/.claude/uploads/...` に置かれる。まず内容を読み込む：
```bash
python -c "import knowledge_base; print(knowledge_base._read_pdf('/root/.claude/uploads/<hash>/<file>.pdf'))"
```

---

### 実行フロー（7フェーズ）

フェーズを順番に実行し、各エージェントとして思考・出力する。

#### Phase 0: Creative Brief 作成（ECD）【必須・最初のアウトプット】

**ブリーフを読んだら、他の何より先にCreative Briefをユーザーに提示する。これが出るまで次のフェーズに進まない。**

以下20フィールドのCreative Briefを作成し、表形式でそのままチャットに出力する。
campaign_concept / campaign_tagline / key_visual / catch_copy は後工程で埋めるため **TBD** のままにする。

| フィールド | 内容 |
|---|---|
| brand_name | ブランド名 |
| brand_philosophy | ブランドの哲学・社会的役割 |
| brand_slogan | ブランドの宣誓 |
| brand_promise | ブランドが生活者に約束すること |
| business_goal | ビジネスゴール |
| ad_role | 広告が果たす役割 |
| problem | 商品・ブランドの課題 |
| competitor | 競合と差異 |
| usp | FACT × BENEFIT = 消費者への約束 |
| fact | USPを裏付ける事実 |
| target | ターゲット（デモグラ＋サイコグラフィクス） |
| target_insight | 潜在的欲求（必ず「実は〜」の形で） |
| social_insight | 社会環境・社会的課題 |
| before_perception | 現状のブランドへの認識 |
| after_perception | このキャンペーンで作りたい認識 |
| tone_and_manner | 守るべきトーン・禁じ手 |
| campaign_concept | TBD |
| campaign_tagline | TBD |
| key_visual | TBD |
| catch_copy | TBD |

#### Phase 0b: ECD ブリーフ解析
- 前提の解体（疑うべき仮定に★）
- 本質的な課題（クライアントが言っていることとのギャップ）
- 書き換えられた問い（「〇〇を伝えたい」→「〇〇という問いを社会に投げかけたい」）を**複数案**出す
- 禁じ手リスト（このカテゴリーが繰り返してきた陳腐なアプローチ3つ）

#### Phase 1: Researcher
**WebSearch ツールを積極的に使う。**
1つのインサイトに絞らず、**可能性のある方向性を3〜4つ並べる**。

- 競合白地マップ：誰もやっていないポジション・感情・価値観（複数列挙）
- **インサイト仮説を3〜4案**並べる（各案：「実は〜」の形・裏付けとなる観察・確信度）
- 可能性のある文化的緊張（A案・B案・C案として並べる）
- 各方向性の「面白さの理由」と「リスク」をセットで提示
- まだ1つに絞らない。絞るのはPhase 3のECDの仕事

#### Phase 2: Strategic Planner
**WebSearch ツールで外部データを検索する（必須）。**
検索先：博報堂生活総研（seikatsusoken.jp/teiten/）・電通（dentsu.co.jp/knowledge/）・NRI・総務省・内閣府・厚労省・経産省・NHK文研

- 市場・生活者データサマリー（出典付き）
- データが示す「複数の解釈」を並べる（データから1つの結論に急がない）
- 戦略テリトリー候補を**2〜3案**提示（各案：方向性・根拠データ・異業種移植アイデア）
- 各テリトリーの強みと死角をセットで提示

#### Phase 3: ECD — 戦略方向性マップ＆テリトリー選択
Phase 0b・1・2を統合して**方向性マップ**を作る。先にCDブリーフに進まない。

- 可能性のある戦略方向性を**3案**並べる（各案にタイトル・一行説明・なぜ面白いか・なぜ難しいか）
- 各案の「どのインサイトを使うか」「どの禁じ手を回避するか」を明示
- **最も強い1案を選択し、選んだ理由と捨てた理由を明記する**

#### Phase 4: ECD — CDブリーフ生成
選択した方向性をCDへの指示に変換する。
書き換えられた問い・禁じ手リスト・最強インサイト・異業種移植・期待水準を含める。

#### Phase 5: CD → クリエイティブパッケージ
以下の専門家として順番にアウトプットする。

**CopyWriter：**
```bash
python -c "from agent_team import _fetch_tcc_copy; print(_fetch_tcc_copy('キーワード'))"
```
でTCC検索（6万件の受賞コピーDB）を使い、コピーの方向性を複数提案する。

**Art Director：** ビジュアルコンセプト・色・タイポグラフィ・撮影スタイル・ヒーロービジュアル描写

**Activation Planner：** 消費者ジャーニー・チャネル戦略・キーアクティベーション・日本固有の接点設計

**PR Planner：** PRコアメッセージ・ニュースフック・メディア別アプローチ・拡散設計

#### Phase 6: Challenger
CDアウトプットを攻撃する。遠慮しない。
- 陳腐化している点（日本広告の典型パターンとの照合）
- このカテゴリーの白地
- 次のラウンドで踏み込むべき方向（2〜3案）

#### Phase 7: ECD ファイナルディレクション
全アウトプットを統合してファイナルディレクションを出す。
Creative BriefのTBD欄（campaign_concept / campaign_tagline / key_visual / catch_copy）を埋める。

#### HTML出力
全フェーズのアウトプットをHTMLにまとめて `output/` に保存する。
`save_output.py` を使う：
```bash
python save_output.py "<ブリーフ>" '<JSON形式のCreativeBrief>' '<全アウトプット>'
```
または Write ツールで直接 `output/YYYYMMDD_HHMMSS_<slug>.html` に書き出す。

完了したらファイルパスをユーザーに伝える。

---

### 理論書HTMLを生成する（APIキー不要）

```bash
python main.py --theory
```

`docs/index.html` と `output/theory.html` に最新版が生成される。
`knowledge/宮崎太郎のクリエイティブ論/` 以下のMarkdownを更新したら必ず再実行してcommit/pushする。

---

### 発見・知見をリポジトリに蓄積する

セッション中に「普遍化できる発見」が生まれたら、クライアント名・固有情報を除いてリポジトリに残す：

- クリエイティブの原則・法則・構造的パターン
- 「なぜこれが機能したか」の構造的な分析
- 広告・マーケティング・チームデザインに関する新しい視点

**書き先：**
- `knowledge/宮崎太郎のクリエイティブ論/発見ログ/YYYY.md` — 時系列の発見メモ
- `knowledge/宮崎太郎のクリエイティブ論/原則/` — 再現可能な原則として独立させる価値があるもの
- `knowledge/宮崎太郎のクリエイティブ論/_overview.md` — 理論の全体像が更新されるとき

**判断基準：** 「このブリーフがなくても成立する話か？」→ YESなら残す価値がある。

commit して push する。

---

## AIに任せていいもの

- 情報収集・競合整理・論点整理
- 既存表現のパターン出し・初期コピー案・構成案
- 打ち合わせメモの要約・ブリーフの複数解釈
- 企画の穴探し・表現の言い換え・資料のたたき台
