# pitest_utils.py
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from op_configs import SCRIPT_DIR

PIT_REPORT_DIR = SCRIPT_DIR / "pit-reports"

def extract_pitest_sections(output: str) -> Tuple[Optional[str], Optional[str]]:
    lines = output.splitlines()
    timings_start = next((i for i, l in enumerate(lines) if l.strip().startswith("- Timings")), None)
    stats_start   = next((i for i, l in enumerate(lines) if l.strip().startswith("- Statistics")), None)

    timings_block = None
    if timings_start is not None:
        collected = []
        for line in lines[timings_start + 1:]:
            s = line.lstrip()
            if s.startswith(">"):
                collected.append(line)
                if s.startswith("> Total"):
                    break
        timings_block = "\n".join(collected)

    statistics_block = None
    if stats_start is not None:
        collected = []
        for line in lines[stats_start + 1:]:
            s = line.lstrip()
            if s.startswith(">>"):
                collected.append(line)
                if s.startswith(">> Ran"):
                    break
        statistics_block = "\n".join(collected)

    return timings_block, statistics_block

def append_pitest_results(api_name: str,
                          operation: str,
                          mode: str,
                          level: str,
                          strength: str,
                          timings: str,
                          statistics: str) -> None:
    rep_file = PIT_REPORT_DIR / api_name / f"{operation}_{mode}_{level}_{strength}.txt"
    rep_file.parent.mkdir(parents=True, exist_ok=True)
    with open(rep_file, "w", encoding="utf-8") as f:
        f.write(f"===== API: {api_name} =====\n")
        f.write(f"===== Operation: {operation} =====\n")
        f.write(f"===== Mode: {mode} =====\n")
        f.write(f"===== Level: {level} =====\n")
        f.write(f"===== Strength: {strength} =====\n\n")
        f.write("===== Pitest Timings =====\n")
        f.write(timings + "\n\n")
        f.write("===== Pitest Statistics =====\n")
        f.write(statistics + "\n\n")
