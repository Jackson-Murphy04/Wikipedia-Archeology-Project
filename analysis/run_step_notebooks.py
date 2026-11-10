"""Execute notebook code cells in order when a Jupyter kernel is unavailable."""
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("MPLBACKEND", "Agg")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
PROJECT = Path(__file__).resolve().parent.parent
ANALYSIS = PROJECT / "analysis"
os.chdir(PROJECT)
sys.path.insert(0, str(ANALYSIS))

requested = [ANALYSIS / sys.argv[1]] if len(sys.argv) > 1 else sorted(ANALYSIS.glob("step*.ipynb"))
for notebook_path in requested:
    if not notebook_path.is_file():
        raise FileNotFoundError(notebook_path)
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    namespace = {"__name__": "__main__"}
    print(f"Executing {notebook_path.name}", flush=True)
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        try:
            exec(compile(source, f"{notebook_path.name}:cell-{index + 1}", "exec"), namespace)
        except Exception as exc:
            raise RuntimeError(f"Failed in {notebook_path.name}, cell {index + 1}: {exc}") from exc
    print(f"Completed {notebook_path.name}", flush=True)
