"""
Claude Code がエージェントチームとして直接動いた結果を HTML に保存するスクリプト。
python main.py を使わず、このチャット上で生成したアウトプットを保存する用途。

使い方：
  from save_output import save_html
  path = save_html(brief="...", creative_brief={...}, sections=[("ECD", "..."), ...], final="...")
"""

import html as html_module
import json
import re
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"


def _md(text: str) -> str:
    t = html_module.escape(text)
    t = re.sub(r"^### (.+)$", r"<h3>\1</h3>", t, flags=re.MULTILINE)
    t = re.sub(r"^## (.+)$", r"<h2>\1</h2>", t, flags=re.MULTILINE)
    t = re.sub(r"^# (.+)$", r"<h1>\1</h1>", t, flags=re.MULTILINE)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"^[-•] (.+)$", r"<li>\1</li>", t, flags=re.MULTILINE)
    t = re.sub(r"(<li>.*?</li>\n?)+", lambda m: f"<ul>{m.group()}</ul>", t, flags=re.DOTALL)
    t = re.sub(r"^\|(.+)\|$", lambda m: "<tr>" + "".join(
        f"<td>{c.strip()}</td>" for c in m.group(1).split("|")
    ) + "</tr>", t, flags=re.MULTILINE)
    t = re.sub(r"(<tr>.*?</tr>\n?)+", lambda m: f"<table>{m.group()}</table>", t, flags=re.DOTALL)
    t = re.sub(r"<tr><td>-+</td>.*?</tr>", "", t)
    t = re.sub(r"^---+$", r"<hr>", t, flags=re.MULTILINE)
    t = re.sub(r"\n{2,}", "</p><p>", t)
    t = re.sub(r"\n", "<br>", t)
    return f"<p>{t}</p>"


def _brief_html(cb: dict) -> str:
    if not cb:
        return ""
    FIELDS = [
        ("Brand Name", "brand_name"),
        ("Brand Philosophy", "brand_philosophy"),
        ("Brand Slogan", "brand_slogan"),
        ("Brand Promise", "brand_promise"),
        ("Business Goal", "business_goal"),
        ("Ad Role", "ad_role"),
        ("Problem", "problem"),
        ("Competitor", "competitor"),
        ("USP", "usp"),
        ("Fact", "fact"),
        ("Target", "target"),
        ("Target Insight", "target_insight"),
        ("Social Insight", "social_insight"),
        ("Before Perception", "before_perception"),
        ("After Perception", "after_perception"),
        ("Tone & Manner", "tone_and_manner"),
        ("Campaign Concept", "campaign_concept"),
        ("Campaign Tagline", "campaign_tagline"),
        ("Key Visual", "key_visual"),
        ("Catch Copy", "catch_copy"),
    ]
    left = FIELDS[:10]
    right = FIELDS[10:]
    cells = ""
    for (ll, lk), (rl, rk) in zip(left, right):
        lv = cb.get(lk, "")
        rv = cb.get(rk, "")
        lc = "tbd" if lv in ("", "TBD") else ""
        rc = "tbd" if rv in ("", "TBD") else ""
        cells += f"""<div class="brief-cell">
  <div class="brief-label">{html_module.escape(ll)}</div>
  <div class="brief-value {lc}">{html_module.escape(lv or "—")}</div>
</div>
<div class="brief-cell">
  <div class="brief-label">{html_module.escape(rl)}</div>
  <div class="brief-value {rc}">{html_module.escape(rv or "—")}</div>
</div>"""
    return f"""<div class="brief-wrap">
  <div class="brief-title">C R E A T I V E &nbsp; B R I E F</div>
  <div class="brief-grid">{cells}</div>
</div>"""


def save_html(
    brief: str,
    creative_brief: dict,
    sections: list[tuple[str, str]],
    final: str,
) -> Path:
    """
    brief          : 元ブリーフ文字列
    creative_brief : 20フィールドのdict
    sections       : [(agent_name, output_text), ...] のリスト
    final          : ECDファイナルディレクション
    戻り値: 保存先Path
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^\w぀-鿿]", "_", brief[:30]).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{timestamp}_{slug}.html"

    generated_at = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    agent_cards = ""
    for name, output in sections:
        agent_cards += f"""
<div class="agent-card">
  <div class="agent-header"><span class="agent-name">{html_module.escape(name)}</span></div>
  <div class="agent-body">{_md(output)}</div>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>クリエイティブアウトプット — {html_module.escape(brief[:60])}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Hiragino Sans", "Yu Gothic", sans-serif; background: #f5f5f0; color: #1a1a1a; line-height: 1.8; }}
  .page {{ max-width: 960px; margin: 0 auto; padding: 48px 24px; }}
  header {{ border-bottom: 3px solid #1a1a1a; padding-bottom: 24px; margin-bottom: 48px; }}
  header h1 {{ font-size: 1.1rem; font-weight: 600; letter-spacing: .08em; color: #555; margin-bottom: 8px; }}
  header p {{ font-size: 1.4rem; font-weight: 700; line-height: 1.5; }}
  .meta {{ font-size: .8rem; color: #888; margin-top: 8px; }}
  .section-title {{ font-size: .75rem; font-weight: 700; letter-spacing: .12em; color: #888; text-transform: uppercase; margin-bottom: 20px; }}
  .agent-card {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
  .agent-header {{ padding: 14px 20px; background: #fafafa; border-bottom: 1px solid #e0e0e0; }}
  .agent-name {{ font-weight: 700; font-size: .95rem; }}
  .agent-body {{ padding: 20px; font-size: .9rem; }}
  .agent-body h1, .agent-body h2, .agent-body h3 {{ margin: 1em 0 .5em; font-weight: 700; }}
  .agent-body h2 {{ font-size: 1.05rem; border-bottom: 1px solid #eee; padding-bottom: 4px; }}
  .agent-body ul {{ padding-left: 1.4em; margin: .5em 0; }}
  .agent-body li {{ margin-bottom: .3em; }}
  .agent-body table {{ width: 100%; border-collapse: collapse; margin: 1em 0; font-size: .88rem; }}
  .agent-body td {{ border: 1px solid #e0e0e0; padding: 8px 12px; }}
  .agent-body strong {{ font-weight: 700; }}
  .agent-body hr {{ border: none; border-top: 1px solid #eee; margin: 1em 0; }}
  p {{ margin: .6em 0; }}
  .final {{ background: #1a1a1a; color: #f5f5f0; border-radius: 8px; padding: 36px; margin-top: 48px; }}
  .final .section-title {{ color: #aaa; }}
  .final-body {{ font-size: 1rem; line-height: 1.9; margin-top: 16px; }}
  .final-body h2 {{ font-size: 1.1rem; border-bottom: 1px solid #444; padding-bottom: 4px; margin: 1.2em 0 .5em; color: #fff; }}
  .final-body ul {{ padding-left: 1.4em; margin: .5em 0; }}
  .final-body li {{ margin-bottom: .3em; }}
  .final-body strong {{ color: #fff; }}
  .final-body hr {{ border: none; border-top: 1px solid #444; margin: 1em 0; }}
  .brief-wrap {{ background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 36px; margin-bottom: 48px; }}
  .brief-title {{ font-size: .75rem; font-weight: 700; letter-spacing: .2em; text-align: center; margin-bottom: 28px; color: #1a1a1a; }}
  .brief-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; border-top: 1px solid #ccc; border-left: 1px solid #ccc; }}
  .brief-cell {{ border-right: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 12px 16px; font-size: .85rem; line-height: 1.6; }}
  .brief-label {{ font-weight: 700; color: #c0392b; font-size: .78rem; letter-spacing: .04em; margin-bottom: 4px; }}
  .brief-value {{ color: #1a1a1a; white-space: pre-wrap; }}
  .brief-value.tbd {{ color: #aaa; font-style: italic; }}
</style>
</head>
<body>
<div class="page">
  <header>
    <h1>クリエイティブアウトプット</h1>
    <p>{html_module.escape(brief)}</p>
    <div class="meta">生成日時：{generated_at}</div>
  </header>

  {_brief_html(creative_brief)}

  <div class="section-title">各エージェントのアウトプット</div>
  {agent_cards}

  <div class="final">
    <div class="section-title">ECDファイナルディレクション</div>
    <div class="final-body">{_md(final)}</div>
  </div>
</div>
</body>
</html>"""

    path.write_text(html, encoding="utf-8")
    return path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python save_output.py '<brief>' '<brief_json>' '<sections_json>' '<final>'")
        sys.exit(1)
    brief = sys.argv[1]
    cb = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    secs_raw = json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
    final = sys.argv[4] if len(sys.argv) > 4 else ""
    out = save_html(brief, cb, secs_raw, final)
    print(out)
