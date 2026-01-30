from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
patterns = ('*.json', '*.ts', '*.tsx')

skip_dirs = {"node_modules", ".venv", "dist", "out"}

files = []
for pattern in patterns:
    for p in root.rglob(pattern):
        if any(part in skip_dirs for part in p.parts):
            continue
        if not p.is_file():
            continue
        data = p.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            files.append(p)

for p in files:
    text = p.read_text(encoding="utf-8-sig")
    p.write_text(text, encoding="utf-8")

print(f"removed BOM from {len(files)} files")
for p in files:
    print(p)

if len(files) > 0:
    sys.exit(0)
