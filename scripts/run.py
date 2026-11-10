
import subprocess
import sys
from pathlib import Path

# Directory containing this script
BASE = Path(__file__).resolve().parent

# Scripts to execute in order
SCRIPTS = [
    "../historical_analysis/collect_history.py",
    "../historical_analysis/clean_historical.py",
    "../historical_analysis/analyze_history.py",
]

def main():
    print("=" * 60)
    print("STARTING WIKIPEDIA ARCHAEOLOGY PIPELINE")
    print("=" * 60)

    for i, script in enumerate(SCRIPTS, start=1):
        script_path = (BASE / script).resolve()

        if not script_path.exists():
            print(f"\nERROR: Script not found: {script_path}")
            sys.exit(1)

        print(f"\n[{i}/{len(SCRIPTS)}] Running {script}")
        print("-" * 60)

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=BASE
        )

        if result.returncode != 0:
            print(f"\nERROR: {script} failed with exit code {result.returncode}")
            print("Pipeline stopped.")
            sys.exit(result.returncode)

        print(f"\nCompleted: {script}")

    print("\n" + "=" * 60)
    print("ALL PIPELINE SCRIPTS COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
