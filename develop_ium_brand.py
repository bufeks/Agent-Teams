"""
ium FY26-28 Brand Communication Plan Developer

PDFの作りかけ資料をベースに、Agent APIで完成版ブランドコミュニケーションプランを生成する。
"""

import anthropic
import sys
import os

PDF_PATH = "/root/.claude/uploads/938b660b-5fd4-4a6a-bf57-9dcb7ef6639f/ec201059-260508_ium202628_Plan_ALL.pdf"
OUTPUT_PATH = "/home/user/Agent-Teams/output/ium_FY2628_brand_plan_complete.md"

PDF_CONTENT_SUMMARY = """
# ium FY26-28 Brand Communication — 既存資料の内容整理

## 文書の状態
- 作成日: 2026.05.08 / by kiCk inc.
- 状態: 作りかけ（以下のセクションが未完成・未着手）

## INDEX
1. iumの現状と課題 ← ほぼ完成
2. iumブランドを定義する ← 検討案複数あり、結論未確定
3. 販売プラットフォーム別の顔つきのコントロール ← 未着手
4. プロモーション具体案 ← 未着手
5. 予算表 ← 「さいごにやる」と明記、未着手

---

## Section 1: iumの現状と課題（既存コンテンツ）

### iumが目指す未来
- 27年以降、iumはECブランドから「高価格帯美容家電ブランド」へ拡張
- 27年：家電量販店で高価格帯商品を展開
- 28年：髭剃りや新製品も含めてさらに拡張
- 必要なのは「量販店でも選ばれる高機能パーソナルケア家電ブランドとしての認知とポジション」

### ECの限界
- ECのオペレーションだけで伸ばすフェーズは限界に近い
- 低価格ラインナップ：Amazon内でのスイッチングが見込める（アイロン、ドライヤー、マルチトリマー）
- 高価格ラインナップ：Amazon内でのスイッチングが難しい（スピードショット、ヘッドスパ）
- 次の成長レバーは「指名検索を増やすこと」

### ブランド認知率の不足
- 認知が購買理由の強い要因でなくなるのは30%を超えてからが一つの目安
- iumの現状認知: 18% / 興味: 10% / 購入意向: 9% / 好意: 7%
- 競合比較: パナソニック83%、ブラウン54%、フィリップス50%、ヤーマン45%、サロニア35%、Nobby(テスコム)24%

### 「メンズ」キーワード売上の重要性
- 現状の主要売上は「メンズ」掛け合わせキーワードからの流入
- 女性獲得に向けてここを落とさないように

### 男性市場の評価
- 「男性市場を取り切った」ではなく「現状認知の中では取り切っている」と捉える
- Nobbyとの差は商品力だけでなく、ブランド認知・検索想起の差
- 「男性起点のまま、どこまで市場を広げられるか」も再検討の余地あり

---

## Section 2: iumブランドを定義する（検討中）

### 大きな選択
「独自性を取るか、間口を取るか」
- メンズを強く出すほど、ブランドの独自性は明確になる。一方でターゲットのパイが狭くなる可能性がある。
- メンズを弱めれば、女性・ユニセックス市場にも広がる。一方でレッドオーシャンの市場でiumの独自性が薄まる可能性がある。
- 「独自性」と「市場拡張性」のバランスをどう設計するか。

### 方向性A：メンズ起点を維持し、表現と価値で間口を広げる
検討中のブランドコンセプト候補（いずれも「検討」マーク）：
- **human beauty gear** — 人を想い、人の願いを叶えるための美容ギア（男女両性への拡張想定）
- **self styling gear** — なりたい自分を叶えるスタイリングギア（男性メイン、女性サブ）
- **self expression gear** — らしさや個性を形にする"自己表現ギア"（男性メイン、女性サブ）
- **self improvement gear** — より魅力的な自分になるための"自分磨きギア"（男性メイン、女性サブ）
- **lifestyling beauty gear** — 人生をスタイリングする美容ギア（男性メイン、女性サブ）
- **The mens beauty standard** — 男性向け美容のスタンダードをつくり続ける（男性特化）
- **MENS BEAUTY CORE** — 男性の美しさの中心を作る（男性特化）

### 方向性B：性別ではない価値で間口を広げる
「男性向け」独自性はあったが、スケールが見込める「強み」にはなりにくい
- 問題①: どんなポジションを狙うことが今後の事業成長に繋がるか？
- 問題②: 何を強みと設定するとブランドへの興味に繋がるか？

### iumポジションの本質的な考察
- iumの独自性とは「男性向けブランドとして磨いた設計思想そのもの」
- 「合理性≒MINIMAL」という思想こそ、ブランドの本来的な価値
- 美容に不慣れな男性でも使い続けやすい、機能的かつ無駄のない設計
- → 「高いユーザビリティ」と「なりたい自分の叶えやすさ」= 性別を問わず享受できる普遍的な価値

### 「合理性」の定義
- 日常に必要な分だけ
- 本質を大切にする
- 過剰でも不足でもない
- 等身大という感覚
- 無駄もなく無理もない
→「この感覚、めっちゃ日本的」→「ノームコア・北欧家具・丁寧な暮らし」的感覚
→「侘び寂び・足るを知る」みたいな

### 検討中のブランドコンセプト候補B群
- **NIPPONIA BEAUTY** — 引き算の美学／足すではなく、整えて美しさを叶える
- **ZEN BEAUTY SYSTEM** — 本質の黒を貫く（とにかく黒いって独自、精神性としての黒=態度）

### 量販店展開の課題：買い方のデザイン
- 「ドンキという買い方が味気ない」
- 商品と向き合った時に「欲しい」と思えるトリガーがない
- どう買うのか、なぜ買うのか、という設定の方を考えたい
→ NIPPON BAUTYとしての美容家電の買い方を開発する（Vermicular Village参照）
→ 真っ黒な茶室的なポップアップでタッチポイント

### 競合ポジショニングマップ（現状認識）
高価格帯＆ブランド認知高：ReFa、DYSON
中価格帯＆中認知：ium（現在地）
中価格帯＆低認知：Nobby
低価格帯＆低認知：SALONIA

### 現行商品ラインナップ
- HAIR DRYER（ヘアドライヤー）「サッと速乾。セットもキメる。」
- HAIR IRON（ヘアアイロン）「指先のような操作性で、ストレートも、カールも。」
- MULTI TRIMMER（マルチトリマー）「刈り上げメンテも、体毛ケアも、これ一本で。」
- SPEED SHOT（スピードショット）「ハイスピードで、超ラク。」（大賞受賞）
- EMS HEAD SPA（EMSヘッドスパ）「パワフル。だから、やみつきに。」

---

## Section 3〜5: 未着手
- Section 3: 販売プラットフォーム別の顔つきのコントロール
- Section 4: プロモーション具体案
- Section 5: 予算表
"""

DEVELOPMENT_PROMPT = f"""あなたはium（マンダムの美容家電ブランド）のFY26-28ブランドコミュニケーションプランを完成させる戦略プランナーです。

## あなたの役割
kiCk inc.のシニアストラテジストとして、以下の作りかけ資料をベースに、クライアント（mandom / ium担当者）に提出できる完成版ドキュメントを作成してください。

## iumブランドの基本情報
{PDF_CONTENT_SUMMARY}

## 完成させるべきドキュメントの要件

### 全体方針
1. kiCk inc.のアプローチ「みえないものをデザインする / Invisible Design, Visible Change」を体現した内容にする
2. 既存のSection 1は内容を整理・補完する
3. Section 2は複数の検討案を整理し、推奨案を1つ選択・理由を明示する
4. Section 3〜5は新規で詳細を作成する
5. FY26（2026年）→ FY27（2027年）→ FY28（2028年）の3年ロードマップとして一貫した論理で構成する

### 各セクションの完成要件

**Section 2: iumブランドを定義する**
- 方向性A / Bの整理と評価
- 推奨するブランドポジション（1案に絞り込み）
- ブランドステートメント（日本語・英語）
- ターゲット定義（コアターゲット + エクスパンドターゲット）
- ブランドエクイティピラミッド（機能的価値 → 情緒的価値 → ブランドパーソナリティ）
- トーン＆マナー（表現ルール）
- 競合との差別化ポイント

**Section 3: 販売プラットフォーム別の顔つきのコントロール**
- EC（Amazon / 公式サイト / 楽天）での打ち出し方
- 家電量販店（FY27展開）での打ち出し方
- ポップアップ / リアルタッチポイントの設計方針
- 各チャネルでのビジュアル・コピーのガイドライン

**Section 4: プロモーション具体案**
- FY26（26年4月〜27年3月）の施策
- FY27（27年4月〜28年3月）の施策（量販店展開開始）
- FY28（28年4月〜29年3月）の施策（拡張期）
- 各施策のKPI・ゴール設定
- メディアミックス戦略
- 指名検索を増やすためのコミュニケーション設計

**Section 5: 予算表（フレーム）**
- 3年間の投資フレーム（目安金額レンジ付き）
- 媒体別・施策別の配分案
- ROI目標の考え方

### アウトプット形式
- マークダウン形式
- 各セクションに見出し、本文、補足を明確に記載
- 表・箇条書きを適切に活用
- 全体で7,000〜10,000文字程度
- 日本語で記述（ブランド用語は英語可）

必ず推奨するブランドポジション・ブランドステートメントに対して、なぜその案を選んだかの理由を明示してください。
「検討」で止まっているものを「決断」として示すことが、この資料完成の最大の役割です。
"""

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Usage: ANTHROPIC_API_KEY=sk-ant-... python3 develop_ium_brand.py")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)

    print("ium FY26-28 Brand Communication Plan を生成中...\n")
    print("=" * 60)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    full_response = ""

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=(
            "あなたはブランド戦略とコミュニケーション設計のエキスパートです。"
            "kiCk inc.のシニアストラテジストとして、クライアントに提出できる"
            "完成度の高い戦略ドキュメントを作成します。"
            "抽象的な概念を具体的なアクションと数値に落とし込む能力を持ち、"
            "「検討中」の案件に対して明確な推奨を行います。"
        ),
        messages=[{"role": "user", "content": DEVELOPMENT_PROMPT}],
    ) as stream:
        for event in stream:
            if hasattr(event, "type"):
                if event.type == "content_block_start":
                    if hasattr(event, "content_block"):
                        if event.content_block.type == "thinking":
                            print("[思考中...]", flush=True)
                        elif event.content_block.type == "text":
                            print("\n[生成開始]\n", flush=True)
                elif event.type == "content_block_delta":
                    if hasattr(event, "delta"):
                        if event.delta.type == "text_delta":
                            text = event.delta.text
                            print(text, end="", flush=True)
                            full_response += text

        final_message = stream.get_final_message()

    header = f"""---
title: ium FY26-28 Brand Communication Plan（完成版）
client: mandom / ium
agency: kiCk inc.
date: 2026.05.12
version: 完成版 v1.0（AI-assisted by Claude）
---

"""

    output_content = header + full_response

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(output_content)

    print(f"\n\n{'=' * 60}")
    print(f"完成版ドキュメントを保存しました: {OUTPUT_PATH}")
    print(f"文字数: {len(full_response):,} 文字")
    print(f"入力トークン: {final_message.usage.input_tokens:,}")
    print(f"出力トークン: {final_message.usage.output_tokens:,}")


if __name__ == "__main__":
    main()
