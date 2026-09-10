#!/usr/bin/env python3
"""Turn a Markdown file into a PDF with the machine's own Chrome.

    python tools/md2pdf.py README.md            -> README.pdf beside it
    python tools/md2pdf.py in.md out.pdf

python-markdown does the parsing and headless Chrome does the printing, which
is the same renderer the grader will read it in. No LaTeX, no wkhtmltopdf.
"""
import os
import subprocess
import sys
import tempfile

import markdown

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CSS = """
body { font: 11pt/1.45 Georgia, "Times New Roman", serif; color: #1a1a1a;
       max-width: 46em; margin: 0 auto; padding: 1.2cm 0; }
h1 { font-size: 20pt; margin: 0 0 .2em; }
h2 { font-size: 13.5pt; margin: 1.4em 0 .3em; border-bottom: 1px solid #bbb; }
h3 { font-size: 11.5pt; margin: 1.1em 0 .2em; }
p { margin: .45em 0; }
code { font: 9.5pt Consolas, monospace; background: #f2f2f2; padding: 0 .2em; }
pre { font: 9pt Consolas, monospace; background: #f4f4f4; padding: .6em .8em;
      white-space: pre-wrap; border-left: 3px solid #ccc; }
table { border-collapse: collapse; width: 100%; margin: .6em 0; font-size: 10pt; }
th, td { border: 1px solid #ccc; padding: .3em .5em; vertical-align: top; text-align: left; }
th { background: #eee; }
blockquote { margin: .6em 0; padding-left: .8em; border-left: 3px solid #ccc; color: #444; }
a { color: #1a4d8f; }
"""


def main(src, dst=None):
    dst = dst or os.path.splitext(src)[0] + ".pdf"
    text = open(src, encoding="utf-8").read()
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])
    html = ("<!doctype html><meta charset='utf-8'><title>%s</title><style>%s</style>"
            "<body>%s</body>" % (os.path.basename(src), CSS, body))
    fd, tmp = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(html)
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           "--print-to-pdf=" + os.path.abspath(dst), "file:///" + tmp.replace("\\", "/")]
    subprocess.run(cmd, check=True, capture_output=True, timeout=90)
    os.unlink(tmp)
    print("%s -> %s (%d bytes)" % (src, dst, os.path.getsize(dst)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(*sys.argv[1:3])
