"""Build a factory handoff ZIP from a clean, identified revision."""
import hashlib
from pathlib import Path
import subprocess
import zipfile
import sys

root = Path(__file__).resolve().parents[1]
def git(*args):
    return subprocess.check_output(["git", "-c", f"safe.directory={root.as_posix()}", *args], cwd=root, text=True).strip()

if git("status", "--porcelain", "--untracked-files=normal"):
    sys.exit("Commit changes before building a release.")
subprocess.run(["npm.cmd", "ci"], cwd=root / "frontend", check=True) if "--ci" in sys.argv else None
subprocess.run(["npm.cmd", "run", "build"], cwd=root / "frontend", check=True)
version = git("rev-parse", "HEAD")
out = root.parent / "factory-releases"
out.mkdir(exist_ok=True)
target = out / f"print-ledger-{version[:12]}.zip"
with zipfile.ZipFile(target.with_suffix(".tmp"), "w", zipfile.ZIP_DEFLATED) as z:
    for name in git("ls-files", "backend/app", "backend/requirements.txt", "backend/requirements-ocr.txt", "operations").splitlines():
        if name.endswith((".py", ".ps1", ".md", "requirements.txt", "requirements-ocr.txt")) and name != "backend/app/public_sandbox.py":
            z.write(root / name, name)
    for path in (root / "frontend/dist").rglob("*"):
        if path.is_file() and path.name != "sandbox.html":
            z.write(path, path.relative_to(root).as_posix())
    z.writestr("VERSION", version)
target.with_suffix(".tmp").replace(target)
print(target, hashlib.sha256(target.read_bytes()).hexdigest())
