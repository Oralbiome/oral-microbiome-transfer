#!/usr/bin/env python3
"""Render canonical PDF and accessible HTML; record hashes to reject stale deploys."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs"
CANONICAL = "https://oralbiome.scarpelli.ai/preprint"


def main():
    common = ["pandoc", "docs/Preprint.md", "--resource-path=.:docs", "--standalone", "--lua-filter=scripts/preprint-tables.lua"]
    subprocess.run(common + ["-o", "docs/Preprint.pdf", "--pdf-engine=xelatex",
                            "-H", "docs/tight.tex", "-V", "geometry:margin=0.65in",
                            "-V", "fontsize=10pt", "-V", "colorlinks=true"], cwd=ROOT, check=True)
    subprocess.run(common + ["-o", "docs/Preprint.html", "--mathml", "--embed-resources",
                            "--template=docs/preprint.html.template",
                            "--metadata", "title=Oral Microbiome Models of Diabetes Status: A Retrospective Audit of Cross-Study Transfer"],
                   cwd=ROOT, check=True)
    # The canonical link is added after Pandoc: with --embed-resources Pandoc would try to fetch
    # any <link href> over the network and inline the fetched page as a data: URI.
    html_path = ROOT / "docs/Preprint.html"
    html = html_path.read_text()
    anchor = '<meta name="description"'
    if html.count(anchor) != 1 or "rel=\"canonical\"" in html:
        raise ValueError("Unexpected preprint head; cannot place canonical link")
    html_path.write_text(html.replace(anchor, '<link rel="canonical" href="' + CANONICAL + '">\n  ' + anchor))
    names = ["docs/Preprint.md", "docs/Preprint.pdf", "docs/Preprint.html", "docs/tight.tex", "docs/preprint.html.template",
             "reports/figures/validation_reconstruction.png", "reports/figures/audited_transfer.png", "scripts/preprint-tables.lua"]
    manifest = {"schema_version": 1, "command": "python scripts/render_preprint.py",
                "sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}}
    (DOC / "Preprint.build.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Rendered canonical PDF + standalone accessible HTML and build manifest.")


if __name__ == "__main__":
    main()
