"""index.html（GitHub Pages 版）から Claude Artifact 用の HTML を作る。
使い方: python3 _tools_build_artifact.py <出力ファイル>
読み込み部分（data.json → Artifact のデータベース）だけ差し替える。"""
import re, sys
src = open("index.html", encoding="utf-8").read()
title = re.search(r"<title>.*?</title>", src).group(0)
links = "\n".join(re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', src))
style = re.findall(r"<style>\n/\* ミス近畿大学.*?</style>", src, flags=re.S)[0]
body = src[src.index('<div class="wrap">'):src.index("<script>")]
js = src[src.index("<script>"):src.index("</script>") + 9]
a = js.index("  /* ---------- データ読み込み")
loader = '''  var C = (typeof window.claude !== "undefined" && window.claude &&
           typeof window.claude.use === "function") ? window.claude : null;
  if (!C) {
    state.ready = true;
    state.error = "この画面ではデータを読み込めません。claude.ai で開いてください。";
    render();
    return;
  }

  C.use("db").then(function (db) {
    if (!db) {
      state.ready = true;
      state.error = "データを読み込めませんでした。claude.ai にログインして開いてください。";
      render();
      return;
    }
    var seen = 0;
    function ready() { seen++; if (seen >= 3) { state.ready = true; render(); } }

    db.doc("meta/config").onSnapshot(function (snap) {
      state.config = snap.exists ? snap.data() : { members: [] };
      if (state.ready) render(); else ready();
    }, function () { });

    db.collection("snapshots").orderBy("measuredAt").onSnapshot(function (qs) {
      state.snaps = qs.docs.map(function (doc) {
        var v = doc.data() || {};
        return { id: doc.id, measuredAt: v.measuredAt || "", label: v.label || "", values: v.values || {} };
      });
      reindex();
      if (state.ready) render(); else ready();
    }, function () { });

    db.collection("votes").orderBy("measuredAt").onSnapshot(function (qs) {
      state.votes = qs.docs.map(function (doc) {
        var v = doc.data() || {};
        return { measuredAt: v.measuredAt || "", ranks: v.ranks || {}, phase: v.phase || "before" };
      });
      if (state.ready) render(); else ready();
    }, function () { ready(); });

    setTimeout(function () { if (!state.ready) { state.ready = true; render(); } }, 6000);
  });
})();
</script>'''
js = js[:a] + loader
out = title + "\n" + links + "\n\n" + style + "\n\n" + body + js + "\n"
out = out.replace('<span class="org" id="updated"></span>\n', '')
open(sys.argv[1], "w", encoding="utf-8").write(out)
print(len(out))
