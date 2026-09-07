"""
tools/build_readme_pdf.py — render README.md to README.pdf.

Markdown to styled HTML to PDF via headless Chromium. The README carries code
blocks, JSON, before/after diffs and four tables, and a print stylesheet keeps
all of them readable on letter paper without reflowing the prose into soup.

    python tools/build_readme_pdf.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "README.md"
DST = ROOT / "README.pdf"

CSS = """
@page { size: letter; margin: 18mm 16mm 20mm 16mm; }
* { box-sizing: border-box; }
body {
  font: 10.5pt/1.5 "Charter", "Georgia", "Times New Roman", serif;
  color: #16181d; margin: 0; -webkit-font-smoothing: antialiased;
}
h1 {
  font-size: 21pt; line-height: 1.15; margin: 0 0 2pt; letter-spacing: -0.01em;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-weight: 700;
}
h1 + p { color: #5b616e; font-size: 10pt; margin-top: 0; }
h2 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 13pt; font-weight: 700; margin: 22pt 0 7pt;
  padding-bottom: 4pt; border-bottom: 1.2pt solid #16181d;
  page-break-after: avoid; letter-spacing: -0.005em;
}
h3 {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 11pt; font-weight: 700; margin: 14pt 0 4pt; color: #2b2f38;
  page-break-after: avoid;
}
p { margin: 0 0 8pt; orphans: 3; widows: 3; }
strong { font-weight: 700; }
hr { border: 0; border-top: 0.6pt solid #d6d9df; margin: 16pt 0; }
a { color: #16181d; text-decoration: none; }

code {
  font-family: "SF Mono", "DejaVu Sans Mono", Menlo, Consolas, monospace;
  font-size: 8.8pt; background: #f2f3f5; padding: 0.5pt 3pt;
  border-radius: 2.5pt; color: #1f2937;
}
pre {
  background: #f7f8fa; border: 0.6pt solid #e2e5ea; border-left: 2.5pt solid #9aa2b1;
  border-radius: 3pt; padding: 8pt 10pt; margin: 0 0 10pt;
  overflow: hidden; page-break-inside: avoid;
}
pre code {
  background: none; padding: 0; font-size: 8.2pt; line-height: 1.42;
  white-space: pre-wrap; word-break: break-word; color: #23272f;
}

table {
  border-collapse: collapse; width: 100%; margin: 0 0 11pt;
  font-size: 9pt; page-break-inside: avoid;
}
th {
  text-align: left; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 8.4pt; text-transform: uppercase; letter-spacing: 0.045em;
  color: #4b5160; border-bottom: 1pt solid #16181d; padding: 4pt 6pt 3pt;
}
td { padding: 4pt 6pt; border-bottom: 0.5pt solid #e4e7ec; vertical-align: top; }
tr:last-child td { border-bottom: 0.8pt solid #b9bec8; }
td:nth-child(n+3) { text-align: right; font-variant-numeric: tabular-nums; }
table td:first-child code { font-size: 8.2pt; }

ul, ol { margin: 0 0 9pt; padding-left: 16pt; }
li { margin-bottom: 3pt; }
blockquote {
  margin: 0 0 10pt; padding: 6pt 12pt; border-left: 2.5pt solid #c3c8d2;
  color: #3c414c; font-style: italic;
}
h2 + p, h3 + p { margin-top: 0; }
"""

HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Rex Machina: The Canon Index</title><style>{css}</style></head>
<body>{body}</body></html>"""


def find_chromium() -> str | None:
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(Path("/").glob(pat.lstrip("/")))
        if hits:
            return str(hits[-1])
    return None


def main() -> int:
    if not SRC.exists():
        print(f"missing {SRC}", file=sys.stderr)
        return 1

    body = markdown.markdown(
        SRC.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    html = HTML.format(css=CSS, body=body)

    binary = find_chromium()
    if not binary:
        print("no chromium found; cannot render PDF", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "readme.html"
        src.write_text(html, encoding="utf-8")
        cmd = [
            binary, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={DST}", src.as_uri(),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if not DST.exists():
            print(r.stderr[-1500:], file=sys.stderr)
            return 3

    print(f"wrote {DST} ({DST.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
