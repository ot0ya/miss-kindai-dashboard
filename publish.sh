#!/bin/zsh
# _export/ の最新データから data.json を作り直し、GitHub Pages に反映する
set -e
cd "$(dirname "$0")"
python3 build_data.py
if git diff --quiet -- data.json; then echo "変更なし"; exit 0; fi
git add data.json
git commit -q -m "データ更新 $(date '+%Y/%m/%d %H:%M')

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q
echo "公開ページに反映しました: https://ot0ya.github.io/miss-kindai-dashboard/"
