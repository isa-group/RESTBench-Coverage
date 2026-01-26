from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Iterable, Tuple, List
from run_evomaster import JACOCO_CLI_PATH

from op_configs import OperationConfig


def collect_jacoco_report_paths(
    module_dir: Path,
) -> Tuple[List[Path], List[Path]]:
    """
    Given a Java module or multi-module project directory, collect all:
      - target/classes      -> classfiles
      - src/main/java       -> sourcefiles

    This function is filesystem-based (no pom parsing), suitable for
    large-scale research pipelines.

    Parameters
    ----------
    module_dir : str or Path
        Path to a Java module or a multi-module project root.

    Returns
    -------
    (classfiles, sourcefiles) : Tuple[List[Path], List[Path]]
        Lists of directories to be used as JaCoCo report inputs.

    Notes
    -----
    - Only production code is collected.
    - Non-existing directories are ignored.
    - Returned paths are absolute and de-duplicated.
    """
    root = Path(module_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Module directory not found: {root}")

    classfiles: List[Path] = []
    sourcefiles: List[Path] = []

    # Walk once; avoid descending into target too deeply
    for p in root.rglob("*"):
        if not p.is_dir():
            continue

        # --- classfiles ---
        # e.g., xxx/target/classes
        if p.name == "classes" and p.parent.name == "target":
            classfiles.append(p.resolve())
            continue

        # --- sourcefiles ---
        # e.g., xxx/src/main/java
        if (
            p.name == "java"
            and p.parent.name == "main"
            and p.parent.parent.name == "src"
        ):
            sourcefiles.append(p.resolve())

    # Deduplicate while preserving order
    def _dedup(paths: List[Path]) -> List[Path]:
        seen = set()
        out = []
        for x in paths:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return _dedup(classfiles), _dedup(sourcefiles)




def build_jacoco_cli_report_cmd(
    *,
    java_bin: str,
    exec_file: Path,
    classfiles: Iterable[Path],
    sourcefiles: Iterable[Path],
    html_dir: Path,
    xml_file: Path,
    csv_file: Path,
    encoding: str = "UTF-8",
) -> List[str]:
    """
    Build a JaCoCo CLI 'report' command.

    All outputs (HTML / XML / CSV) are mandatory.

    Returns a List[str] suitable for subprocess.run(cmd, ...).
    """
    jacococli_jar = JACOCO_CLI_PATH
    exec_file = exec_file.resolve()
    html_dir = html_dir.resolve()
    xml_file = xml_file.resolve()
    csv_file = csv_file.resolve()

    cmd: List[str] = [
        java_bin,
        "-jar",
        str(jacococli_jar),
        "report",
        str(exec_file),
        "--encoding",
        encoding,
        "--html",
        str(html_dir),
    ]

    for cf in classfiles:
        cmd += ["--classfiles", str(Path(cf).resolve())]

    for sf in sourcefiles:
        cmd += ["--sourcefiles", str(Path(sf).resolve())]

    # mandatory outputs
    cmd += ["--xml", str(xml_file)]
    cmd += ["--csv", str(csv_file)]

    return cmd


def run_jacoco_report_cmd(
    cmd: List[str],
    *,
    log_file: Path,
    dry_run: bool = False,
) -> None:
    """
    Run a JaCoCo CLI report command and save stdout/stderr to a log file.

    Parameters
    ----------
    cmd : List[str]
        Command returned by build_jacoco_cli_report_cmd.
    log_file : Path
        File to write combined stdout/stderr logs.
    dry_run : bool
        If True, only print the command without executing.

    Raises
    ------
    RuntimeError
        If the command fails.
    """
    log_file = log_file.resolve()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    cmd_str = " ".join(cmd)

    # Always record the command itself at the top of the log
    with open(log_file, "w", encoding="utf-8") as lf:
        lf.write("[JaCoCo] Command:\n")
        lf.write(cmd_str + "\n")
        lf.write("\n")

    if dry_run:
        with open(log_file, "a", encoding="utf-8") as lf:
            lf.write("[JaCoCo] Dry-run mode, command not executed.\n")
        print(f"[JaCoCo] Dry-run. Log written to {log_file}")
        return

    try:
        with open(log_file, "a", encoding="utf-8") as lf:
            subprocess.run(
                cmd,
                cwd=None,
                stdout=lf,
                stderr=subprocess.STDOUT,
                check=True,
            )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"JaCoCo report command failed (exit={exc.returncode}). "
            f"See log: {log_file}"
        ) from exc


def generate_and_run_jacoco_report_for_operation(
    *,
    op: OperationConfig,
    java_bin: str,
    report_root: Path,
    suffix: str = "",
    dry_run: bool = False,
) -> None:
    """
    Given an OperationConfig, automatically:
      1) collect classfiles / sourcefiles from the SUT module
      2) build a JaCoCo CLI report command
      3) execute the command

    Parameters
    ----------
    op : OperationConfig
        Operation configuration (must expose api.work_dir()).
    java_bin : str
        Path to java executable
    report_root : Path
        Root directory to place report outputs for this operation.
        Subdirectories/files will be created under this path.
    dry_run : bool
        If True, only print the command without executing.
    """
    api = op.api
    sut_path = api.sut_abs_path()

    # 1) collect classfiles / sourcefiles
    classfiles, sourcefiles = collect_jacoco_report_paths(sut_path)

    if not classfiles:
        raise RuntimeError(
            f"No target/classes found under {sut_path}; cannot generate JaCoCo report."
        )
    if not sourcefiles:
        raise RuntimeError(
            f"No src/main/java found under {sut_path}; cannot generate JaCoCo report."
        )

    # 2) prepare output paths 
    report_root = report_root.resolve()

    html_dir = report_root / f"{suffix}_jacoco_html"
    xml_file = report_root / f"{suffix}_jacoco.xml"
    csv_file = report_root / f"{suffix}_jacoco.csv"
    log_file = report_root / f"{suffix}_jacoco.log"

    exec_file = report_root / f"{suffix}_jacoco.exec"
    if not exec_file.exists():
        # raise FileNotFoundError(f"JaCoCo exec file not found: {exec_file}")
        print(f"[JaCoCo] Warning: exec file not found: {exec_file}. Report will be empty.")
        return
    html_dir.mkdir(parents=True, exist_ok=True)
    xml_file.parent.mkdir(parents=True, exist_ok=True)
    csv_file.parent.mkdir(parents=True, exist_ok=True)

    # 3) build report command
    cmd = build_jacoco_cli_report_cmd(
        java_bin=java_bin,
        exec_file=exec_file,
        classfiles=classfiles,
        sourcefiles=sourcefiles,
        html_dir=html_dir,
        xml_file=xml_file,
        csv_file=csv_file,
    )

    # 4) execute
    run_jacoco_report_cmd(
        cmd,
        dry_run=dry_run,
        log_file=log_file
    )

if __name__ == "__main__":
    from op_configs import scout_api, OPS_MAP
    # op = OPS_MAP.get(scout_api)[0]
    for api, _op_list in OPS_MAP.items():
        if api.is_ind:
            continue
        for op in _op_list:
            print(f"handle {op.id}")
            generate_and_run_jacoco_report_for_operation(
                op=op,
                java_bin="java",
                report_root=api.mt_abs_path() / "jacoco",
                suffix="emon",
                dry_run=False
            )
            generate_and_run_jacoco_report_for_operation(
                op=op,
                java_bin="java",
                report_root=api.mt_abs_path() / "jacoco",
                suffix="emoff",
                dry_run=False
            )

    