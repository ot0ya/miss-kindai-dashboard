"""Claude ダッシュボードから書き出した JSON（_export/）を、公開用の data.json にまとめる。
公開するのは 計測日時・ラベル・フォロワー数・エール投票 だけ（メモ欄などは載せない）。"""
import json, glob, os, re
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, "_export")
MEMBERS = ["田中美海", "白石ひより", "三好愛美", "鈴木凛々子", "仲子和里", "山口小巻",
           "高賀音羽", "松本七乃葉", "月城安菜", "公式（メイン）", "公式（スタッフ）"]
PLATFORMS = {"instagram", "threads", "tiktok", "x"}

def label_of(v):
    v = str(v or "")
    if re.fullmatch(r"\d{5}(\.0)?", v):  # スプレッドシートの日付シリアル値 → M/D
        d = datetime(1899, 12, 30) + timedelta(days=float(v))
        return f"{d.month}/{d.day}"
    return v

snaps = []
for f in sorted(glob.glob(os.path.join(EXP, "snapshots", "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    vals = {}
    for m, pv in (d.get("values") or {}).items():
        if m not in MEMBERS or not isinstance(pv, dict):
            continue
        clean = {k: v for k, v in pv.items() if k in PLATFORMS and isinstance(v, (int, float))}
        if clean:
            vals[m] = clean
    if d.get("measuredAt") and vals:
        snaps.append({"measuredAt": d["measuredAt"], "label": label_of(d.get("label")), "values": vals})

votes = []
for f in sorted(glob.glob(os.path.join(EXP, "votes", "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    ranks = {m: {k: r[k] for k in ("pt", "paid", "free", "rank") if k in r}
             for m, r in (d.get("ranks") or {}).items() if m in MEMBERS}
    if d.get("measuredAt") and ranks:
        votes.append({"measuredAt": d["measuredAt"], "ranks": ranks})

snaps.sort(key=lambda s: s["measuredAt"])
votes.sort(key=lambda v: v["measuredAt"])
jst = timezone(timedelta(hours=9))
out = {"generatedAt": datetime.now(jst).strftime("%Y-%m-%dT%H:%M"),
       "config": {"members": MEMBERS}, "snapshots": snaps, "votes": votes}
with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as fp:
    json.dump(out, fp, ensure_ascii=False, separators=(",", ":"))
print(f"snapshots {len(snaps)} / votes {len(votes)} / generatedAt {out['generatedAt']}")
