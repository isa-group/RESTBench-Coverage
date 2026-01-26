from op_configs import SCRIPT_DIR
from pathlib import Path
from typing import Dict, List, Union
import json
import re

# ---------------------------
# Roots
# ---------------------------

# Root directory containing Schemathesis unique reports:
#   SCH_ROOT/<api_name>/<op_id>/junit-*.xml
SCH_ROOT = SCRIPT_DIR / "schemathesis-unique-reports"

# Roots containing EvoMaster-generated tests:
#   EM_*_ROOT/<api_name>/<op_name>/adv/assertall/eval1000(or 10000)/security/schema/Original_faults_Test.java
#
# Naming convention in this code:
#   - EM_ON: EvoMaster withBasicAssertions enabled
#   - EM_OFF: EvoMaster withBasicAssertions disabled
EM_ON_ROOT = SCRIPT_DIR / "evomaster-generated-tests"
EM_OFF_ROOT = SCRIPT_DIR / "evomaster-generated-tests-without-basic-assertions"


# ---------------------------
# Shared helpers
# ---------------------------

def _dedup_keep_order(items: List[str]) -> List[str]:
    """
    Deduplicate a list of strings while preserving the original order.
    """
    seen = set()
    result = []
    for x in items:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def _save_json_to_root(
    data: Dict[str, List[str]],
    root: Path,
    filename: str = "faults.json",
) -> Path:
    """
    Save a dict[str, list[str]] as JSON under the given root directory.

    Output is stable for replication:
      - UTF-8
      - ensure_ascii=False
      - sort_keys=True
    """
    root.mkdir(parents=True, exist_ok=True)
    out_path = root / filename
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    return out_path


# ---------------------------
# Schemathesis: extract '-' blocks from junit XML as plain text
# ---------------------------

def extract_dash_items_from_xml_text(xml_path: Union[str, Path]) -> List[str]:
    """
    Treat the XML file as plain text (no XML parsing).

    Extract text blocks that follow this structural pattern:
      - A block starts with a line that begins with '-'
      - The block continues with subsequent lines that start with whitespace (space or tab)
      - The block ends when a non-indented line is encountered

    Each extracted block is returned as a multi-line string, preserving original line breaks.
    """
    text = Path(xml_path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    items: List[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if line.startswith("-"):
            block = [line.rstrip()]
            i += 1

            while i < n and (lines[i].startswith(" ") or lines[i].startswith("\t") or lines[i] == ""):
                block.append(lines[i].rstrip())
                i += 1

            items.append("\n".join(block))
        else:
            i += 1

    return items


def normalize_item_to_single_line(item: str) -> str:
    """
    Convert a multi-line fault block into a single line by:
      - stripping each line
      - dropping empty lines
      - joining with single spaces
      - normalizing repeated whitespace
    """
    parts = [ln.strip() for ln in item.splitlines() if ln.strip()]
    return " ".join(" ".join(parts).split())


def collect_faults_for_sch(root: Path = SCH_ROOT) -> Dict[str, List[str]]:
    """
    Traverse Schemathesis unique reports and collect fault descriptions.

    For each directory:
        root/<api_name>/<op_id>/

    - Locate the (single) junit-*.xml file, if present
    - Extract all '-' prefixed blocks (with indented continuation lines)
    - Normalize each block into a single-line string
    - Deduplicate faults within the same operation (keep first occurrence)
    - Skip operations with no extracted faults

    Returns:
        "<api_name>-<op_id>" -> [fault_1, fault_2, ...]
    """
    results: Dict[str, List[str]] = {}

    if not root.exists():
        return results

    for api_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        api_name = api_dir.name

        for op_dir in sorted(p for p in api_dir.iterdir() if p.is_dir()):
            op_id = op_dir.name

            junit_files = list(op_dir.glob("junit-*.xml"))
            if not junit_files:
                continue

            # By assumption: there is at most one junit XML per operation directory
            xml_path = junit_files[0]

            raw_items = extract_dash_items_from_xml_text(xml_path)
            norm_items = [normalize_item_to_single_line(x) for x in raw_items]
            norm_items = [x for x in norm_items if x]
            norm_items = _dedup_keep_order(norm_items)

            if norm_items:
                results[f"{api_name}-{op_id}"] = norm_items

    return results


# ---------------------------
# EvoMaster: extract "// Fault<digits>." comment lines from Java files
# ---------------------------

# Matches lines like:
#   // Fault100. HTTP Status 500. GET:/projects
#   // Fault200. Received A Response ... path '/projects'.
#
# Important: "Fault" is immediately followed by digits (no whitespace in between).
_EM_FAULT_LINE_RE = re.compile(r"^\s*//\s*(Fault\d+\.\s*.*)$")


def extract_em_fault_lines_from_java(java_path: Union[str, Path]) -> List[str]:
    """
    Read a Java test file as plain text and extract all fault comment lines.

    Extraction rule:
      - any line matching: // Fault<digits>. <message>

    Returns:
      A list of strings containing the comment content WITHOUT the leading "//".
      Order is preserved as in the file.
    """
    text = Path(java_path).read_text(encoding="utf-8", errors="replace")
    items: List[str] = []

    for line in text.splitlines():
        m = _EM_FAULT_LINE_RE.match(line)
        if m:
            items.append(m.group(1).strip())

    return items


def collect_faults_for_em(root: Path) -> Dict[str, List[str]]:
    """
    Traverse EvoMaster-generated tests and collect fault comment lines.

    Expected file pattern (relative to root):
      <api_name>/<op_name>/adv/assertall/eval1000(or 10000)/security/schema/Original_faults_Test.java

    Implementation strategy:
      - Find all files named "Original_faults_Test.java" under the root (recursive)
      - Infer api_name and op_name from the first two path segments under root
      - Extract all "// Fault<digits>." comment lines
      - Deduplicate faults within the same operation (keep first occurrence)
      - Skip operations with no extracted faults

    Returns:
        "<api_name>-<op_name>" -> [fault_line_1, fault_line_2, ...]
    """
    results: Dict[str, List[str]] = {}

    if not root.exists():
        return results

    for java_path in sorted(root.rglob("Original_faults_Test.java")):
        rel = java_path.relative_to(root)

        # Must have at least: <api_name>/<op_name>/...
        if len(rel.parts) < 2:
            continue

        api_name, op_name = rel.parts[0], rel.parts[1]
        key = f"{api_name}-{op_name}"

        items = extract_em_fault_lines_from_java(java_path)
        items = [x for x in items if x]
        items = _dedup_keep_order(items)

        if items:
            # If multiple matches occur for the same key (unexpected),
            # append while keeping order, then dedup again.
            if key not in results:
                results[key] = items
            else:
                results[key].extend(items)
                results[key] = _dedup_keep_order(results[key])

    return results


# ---------------------------
# Entrypoint
# ---------------------------

if __name__ == "__main__":
    # Schemathesis
    sch_faults = collect_faults_for_sch(SCH_ROOT)
    sch_out = _save_json_to_root(sch_faults, SCH_ROOT, filename="faults.json")
    print(f"Schemathesis fault summary saved to: {sch_out}")

    # EvoMaster (withBasicAssertions enabled)
    em_on_faults = collect_faults_for_em(EM_ON_ROOT)
    em_on_out = _save_json_to_root(em_on_faults, EM_ON_ROOT, filename="faults.json")
    print(f"EvoMaster (withBasicAssertions enabled) fault summary saved to: {em_on_out}")

    # EvoMaster (withBasicAssertions disabled)
    em_off_faults = collect_faults_for_em(EM_OFF_ROOT)
    em_off_out = _save_json_to_root(em_off_faults, EM_OFF_ROOT, filename="faults.json")
    print(f"EvoMaster (withBasicAssertions disabled) fault summary saved to: {em_off_out}")
