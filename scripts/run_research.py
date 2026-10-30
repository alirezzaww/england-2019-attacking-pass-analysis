"""Run the tournament research in dependency order on Windows, macOS or Linux."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
STAGES = [
    "11_tournament_passes_per_game.py",
    "13_minutes_and_shot_quality.py",
    "14_threshold_sensitivity.py",
    "15_kirby_passing_profile.py",
    "16_match_variation.py",
    "17_passing_volume_adjustment.py",
    "18_first_xg_model.py",
    "19_time_window_sensitivity.py",
    "20_pass_location_context.py",
    "scripts/check_evidence.py",
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="Save plots without opening windows")
    args = parser.parse_args()
    env = os.environ.copy()
    if args.headless:
        env["MPLBACKEND"] = "Agg"
    for stage in STAGES:
        print(f"Running {stage}", flush=True)
        subprocess.run([sys.executable, str(ROOT / stage)], cwd=ROOT, env=env, check=True)
    print("Research pipeline and evidence checks completed.")

if __name__ == "__main__":
    main()
