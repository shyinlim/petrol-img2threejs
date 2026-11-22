"""Verify v12 codebase refactoring: modular src/ files, line limits, package.json scripts, and README.md sections."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails = []


def check(name: str, ok: bool, msg: str) -> None:
    print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
    if not ok:
        fails.append(name)


# R1: Modular src/ files and line counts
expected_limits = {
    "src/main.ts": 120,
    "src/scene.ts": 130,
    "src/textures.ts": 220,
    "src/customizeModel.ts": 260,
    "src/pumpParts.ts": 260,
    "src/ui.ts": 220,
    "src/car.ts": 90,
}
for rel, limit in expected_limits.items():
    p = ROOT / rel
    if not p.exists():
        check(f"file:{rel}", False, "missing")
    else:
        lines = len(p.read_text().splitlines())
        check(f"file:{rel}", lines <= limit, f"{lines} lines (limit <= {limit})")

# R2: package.json scripts
pkg = json.loads((ROOT / "package.json").read_text())
scripts = pkg.get("scripts", {})
for s in ("dev", "build", "preview"):
    check(f"pkg:script:{s}", s in scripts, f"scripts[{s!r}] = {scripts.get(s)!r}")

# R3: README.md existence and key sections
readme = ROOT / "README.md"
if not readme.exists():
    check("readme:exists", False, "README.md missing")
else:
    text = readme.read_text()
    check("readme:exists", len(text) >= 400, f"{len(text)} chars")
    for token in ("npm run dev", "src/scene.ts", "src/textures.ts", "src/customizeModel.ts", "src/ui.ts", "?gate=1", "check_ui.py"):
        check(f"readme:{token}", token in text, f"contains {token!r}")

sys.exit(1 if fails else 0)
