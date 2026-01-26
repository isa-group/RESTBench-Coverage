#!/usr/bin/env python3
import sys
import pandas as pd
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("Usage: python filter_invariants.py input.csv")

in_path = Path(sys.argv[1])
out_path = in_path.parent / "invariants.csv"

# Read CSV
df = pd.read_csv(in_path, delimiter=';')

# Confirm tp contains only 0 and 1
if not set(df["tp"].unique()).issubset({0, 1}):
    sys.exit("Error: 'tp' column must contain only 0 or 1")

# Filter tp=1
df = df[df["tp"] == 1]

# Keep only specified columns
cols = ["pptname", "invariant", "invariantType", "variables", "postmanAssertion"]
df[cols].to_csv(out_path, index=False, sep=';')

print(f"Wrote {len(df)} rows to {out_path}")
