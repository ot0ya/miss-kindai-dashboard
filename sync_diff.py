"""マスタースプシ（xlsx書き出し）の実測ログと、ダッシュボードの既存 snapshots を突き合わせ、
新規・変更のスナップショットだけを outdir に JSON で書き出す。
使い方: python3 -I sync_diff.py <download_file_contentの保存ファイル(.xlsx または JSON)> <既存snapshotsフォルダ> <outdir>"""
import json, base64, zipfile, io, re, sys, os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

src, existing, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
if src.endswith(".xlsx"):  # Drive コネクタが xlsx をそのまま保存する場合
    z = zipfile.ZipFile(src)
else:  # {content: base64} の JSON で保存される場合
    d = json.load(open(src))
    z = zipfile.ZipFile(io.BytesIO(base64.b64decode(d["content"])))
ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
wb = ET.fromstring(z.read("xl/workbook.xml"))
rid = [s for s in wb.find("m:sheets", ns) if s.get("name") == "実測ログ"][0].get("{%s}id" % ns["r"])
rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
target = [r.get("Target") for r in rels if r.get("Id") == rid][0]
path = "xl/" + target.lstrip("/").replace("xl/", "")
ss = []
if "xl/sharedStrings.xml" in z.namelist():
    for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
        ss.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
sh = ET.fromstring(z.read(path))

groups = {}
for row in sh.iter("{%s}row" % ns["m"]):
    if row.get("r") == "1":
        continue
    v = {}
    for c in row.findall("m:c", ns):
        t, x, val = c.get("t"), c.find("m:v", ns), None
        if t == "s" and x is not None:
            val = ss[int(x.text)]
        elif t == "inlineStr":
            val = "".join(e.text or "" for e in c.iter("{%s}t" % ns["m"]))
        elif x is not None:
            val = x.text
        v[re.match(r"[A-Z]+", c.get("r")).group()] = val
    A, C, D, E = v.get("A"), v.get("C"), v.get("D"), v.get("E")
    if not A or not C or not D or E in (None, ""):
        continue
    try:
        a, n = float(A), float(E)
    except ValueError:
        continue
    # 日時IDは分の切り捨て（+1秒は浮動小数の誤差よけ）。四捨五入すると既存IDとずれる
    dt = (datetime(1899, 12, 30) + timedelta(days=a) + timedelta(seconds=1)).replace(second=0, microsecond=0)
    did = dt.strftime("%Y%m%d-%H%M")
    g = groups.setdefault(did, {"id": did, "measuredAt": dt.strftime("%Y-%m-%dT%H:%M"),
                                "label": v.get("B") or "", "note": "スプレッドシートから自動同期", "values": {}})
    if v.get("B"):
        g["label"] = v.get("B")
    g["values"].setdefault(C, {})[D.lower()] = int(n) if n == int(n) else n

now = datetime.now().isoformat(timespec="seconds")
os.makedirs(outdir, exist_ok=True)
new = upd = 0
writes = []
for did, g in sorted(groups.items()):
    f = os.path.join(existing, did + ".json")
    if os.path.exists(f):
        e = json.load(open(f))
        if e.get("values") == g["values"]:
            continue
        if did == "20261005-0026":  # 既知の差（ページ側の月城さん分を消さないため書かない）
            continue
        upd += 1; kind = "upd"
    else:
        new += 1; kind = "new"
    g["savedAt"] = now
    fp = os.path.join(outdir, did + ".json")
    json.dump(g, open(fp, "w"), ensure_ascii=False)
    writes.append((did, kind, fp))
print("groups", len(groups), "new", new, "upd", upd)
for w in writes:
    print(*w)
