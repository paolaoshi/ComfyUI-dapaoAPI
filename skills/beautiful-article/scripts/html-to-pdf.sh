#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# html-to-pdf.sh —— 把 Beautiful Article 的单页 HTML 转成 PDF
#
# 用法：
#   bash <skill>/scripts/html-to-pdf.sh [input.html] [output.pdf]
#   bash <skill>/scripts/html-to-pdf.sh                       # 默认 article/article.html → article/article.pdf
#   bash <skill>/scripts/html-to-pdf.sh --help
#
# 前提：本机已装 Chromium / Google Chrome / Brave / Microsoft Edge 之一
# （脚本会自动探测）。无需 npm 包、无需 Node。
#
# 设计要点（详见 references/pdf-output.md）：
#   1. reacticle 默认 TOC 在桌面是左右栅格；PDF 需要 TOC 上、正文下的上下排布。
#   2. 脚本在 HTML 头部注入一段 @media print CSS 覆盖：把 TOC 塌成一列、解除
#      sticky、长 TOC 双列省纸、TOC 后强制分页、隐藏 colophon 之外的页眉页脚等。
#   3. 用 headless 浏览器 --print-to-pdf 渲染（执行页面 JS，Raw 交互渲染为初始
#      态）；输出标准 A4 / 主题纸色满版背景 + 0.45in 内容留白，无浏览器自带页眉页脚。
#   4. 失败回退：打印"用浏览器手动 Cmd+P → 另存为 PDF"指引，并把注入后的 HTML
#      留在临时目录方便用户自己打印。
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSS_FILE="$SCRIPT_DIR/pdf-print-overrides.css"

INPUT="${1:-article/article.html}"
OUTPUT="${2:-article/article.pdf}"

if [[ "$INPUT" == "--help" || "$INPUT" == "-h" ]]; then
  sed -n '2,21p' "$0"
  exit 0
fi

if [[ ! -f "$INPUT" ]]; then
  echo "✗ 输入文件不存在：$INPUT" >&2
  echo "  先在工作区跑 npm run html 产出 article/article.html。" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

# ── 探测可用的 chromium-family 浏览器 ─────────────────────
find_browser() {
  local candidates=(
    chromium
    chromium-browser
    google-chrome
    google-chrome-stable
    chrome
    brave-browser
    microsoft-edge
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    "/Applications/Arc.app/Contents/MacOS/Arc"
    "/usr/bin/chromium"
    "/usr/bin/google-chrome"
    "/snap/bin/chromium"
  )
  for c in "${candidates[@]}"; do
    if command -v "$c" >/dev/null 2>&1; then
      echo "$c"; return 0
    fi
    if [[ -x "$c" ]]; then
      echo "$c"; return 0
    fi
  done
  return 1
}

# ── 注入 @media print 覆盖到一个临时 HTML ─────────────────
# 设计：CSS 抽到 scripts/pdf-print-overrides.css（详见该文件顶部注释），这里只
# 负责"把它的内容包在 <style> 里、塞到 </head> 之前"。这样：
#   • macOS BSD awk 不接受 -v 传多行字符串（"newline in string"），用 awk
#     getline 从文件读则两边都吃得下。
#   • CSS 文件可独立编辑 / lint / 复用，不被 shell 转义吃掉。
TMP_DIR="$(mktemp -d -t beautiful-article-pdf.XXXXXX)"
TMP_HTML="$TMP_DIR/article-print.html"

if [[ ! -f "$CSS_FILE" ]]; then
  echo "✗ 找不到打印覆盖 CSS：$CSS_FILE" >&2
  echo "  这个文件应跟脚本同目录（scripts/pdf-print-overrides.css）。" >&2
  exit 2
fi

awk -v css_file="$CSS_FILE" '
  /<\/head>/ && !done {
    print "<style id=\"ra-pdf-overrides\">"
    while ((getline line < css_file) > 0) print line
    close(css_file)
    print "</style>"
    done = 1
  }
  { print }
' "$INPUT" > "$TMP_HTML"

if ! grep -q 'ra-pdf-overrides' "$TMP_HTML"; then
  echo "✗ 注入失败：未在输入 HTML 找到 </head>。" >&2
  echo "  你的 article.html 可能不是 Vite + reacticle 单页产物。" >&2
  exit 3
fi

# ── 找浏览器 ──────────────────────────────────────────────
BROWSER="$(find_browser || true)"
if [[ -z "$BROWSER" ]]; then
  echo "⚠ 未找到任何 chromium-family 浏览器（chromium / google-chrome / brave / edge）。"
  echo
  echo "  回退方案：注入了打印 CSS 的 HTML 已经放在："
  echo "  $TMP_HTML"
  echo
  echo "  请用浏览器打开它 → Cmd+P / Ctrl+P → 目标改为'另存为 PDF' → 保存。"
  echo "  注入的 print 样式会让 TOC 在上、正文在下，与 PDF 阅读习惯对齐。"
  exit 3
fi

echo "▸ 用浏览器：$BROWSER"
echo "▸ 输入：$INPUT"
echo "▸ 输出：$OUTPUT"

# ── 渲染 ──────────────────────────────────────────────────
# Chromium 系都支持 --headless --print-to-pdf。
# --no-pdf-header-footer：去掉浏览器自带的 URL / 日期 / 页码（colophon 已有）。
# --virtual-time-budget：给页面 JS 一点时间初始化 Raw 组件（5s 兜底）。
# --hide-scrollbars：避免在 PDF 里看到滚动条残影。
"$BROWSER" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --hide-scrollbars \
  --no-pdf-header-footer \
  --virtual-time-budget=5000 \
  --print-to-pdf-no-header \
  --print-to-pdf="$OUTPUT" \
  "file://$TMP_HTML" 2>/dev/null || {
    # 旧版 Chrome 不认 --headless=new，回退老 flag
    "$BROWSER" \
      --headless \
      --disable-gpu \
      --no-sandbox \
      --hide-scrollbars \
      --print-to-pdf-no-header \
      --print-to-pdf="$OUTPUT" \
      "file://$TMP_HTML" 2>/dev/null
  }

# 清理临时（HTML 注入留作回退证据，最后再清）
rm -rf "$TMP_DIR"

if [[ -f "$OUTPUT" ]]; then
  SIZE="$(du -h "$OUTPUT" | cut -f1)"
  echo "✓ PDF 输出：${OUTPUT} (${SIZE})"
  echo
  echo "  如果 TOC / 分页不理想，看 references/pdf-output.md 故障排除段。"
else
  echo "✗ 浏览器返回成功但输出文件不存在：$OUTPUT" >&2
  exit 4
fi
