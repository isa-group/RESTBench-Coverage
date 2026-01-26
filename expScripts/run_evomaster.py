#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI wrapper for:
  1) Running local OperationTest (via Maven) to start/verify the SUT
  2) Launching EvoMaster in black-box mode for a configured operation

This version simplifies CLI options:
- Output directory is automatically set to ROOT_DIR/evo/{api_name}/{operation_id}/
- Java command is fixed to "java"
- Fixed EvoMaster parameters: output_format=JUNIT, problem_type=REST, seed=42, no JVM opts/log file

Example
-------
# Run OperationTest only
python run_evomaster.py op-test \
    --api ScoutAPI \
    --operation postActivities

# Run EvoMaster black-box
python run_evomaster.py evomaster \
    --api ScoutAPI \
    --operation postActivities \
    --evomaster-jar ~/tools/evomaster.jar \
    --host-url http://localhost:8080
"""

from __future__ import annotations

import os
import re
import shlex
import signal
import subprocess
import sys
from pathlib import Path
import threading
import time
from typing import Iterable, Optional

import click

from exec_utils import make_java_env
from op_configs import OPS_MAP, ApiConfig, OperationConfig, JdkVersion, SCRIPT_DIR, ROOT_DIR

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------
OPERATION_TEST_CLASS = "OperationTest"
EM_JAR = SCRIPT_DIR / "evo" / "evomaster.jar"

# OUTPUT_ROOT = ROOT_DIR.parent / "evomaster-generated-tests" / "src" / "test" / "java"
WITH_BASIC_ASSERTIONS_OUTPUT_ROOT = SCRIPT_DIR / "evomaster-generated-tests"
WITHOUT_BASIC_ASSERTIONS_OUTPUT_ROOT = SCRIPT_DIR / "evomaster-generated-tests-without-basic-assertions"

WITH_BASIC_ASSERTIONS_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
WITHOUT_BASIC_ASSERTIONS_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

JACOCO_AGENT_PATH = SCRIPT_DIR / "tools" / "jacocoagent.jar"
JACOCO_CLI_PATH = SCRIPT_DIR / "tools" / "jacococli.jar"

FIXED_OUTPUT_FORMAT = "JAVA_JUNIT_5"
FIXED_PROBLEM_TYPE = "REST"
FIXED_SEED = 42
FIXED_JVM_OPTS: list[str] = []

PORT_REGEXS = {
    "ScoutAPI": ("Jetty server started on port: (\d+)",),

}

def _available_api_names() -> Iterable[str]:
    """Return available API names defined in OPS_MAP."""
    return sorted(api.name for api in OPS_MAP.keys())


def _available_operation_ids(api: ApiConfig) -> Iterable[str]:
    """Return available operation IDs for a given API."""
    return sorted(op.id for op in OPS_MAP.get(api, []))


def _resolve_operation_config(api_name: str, operation_id: str) -> OperationConfig:
    """Resolve (api, operation) pair to an OperationConfig."""
    for api, operations in OPS_MAP.items():
        if api.name != api_name:
            continue
        for op in operations:
            if op.id == operation_id:
                return op
        available = ", ".join(_available_operation_ids(api))
        raise click.BadParameter(
            f"Unknown operation '{operation_id}' for API '{api_name}'. "
            f"Available operations: {available}",
            param_hint="--operation",
        )
    available = ", ".join(_available_api_names())
    raise click.BadParameter(
        f"Unknown API '{api_name}'. Available APIs: {available}",
        param_hint="--api",
    )


def _operation_test_exists(api: ApiConfig) -> bool:
    """Check if OperationTest.java or OperationTest.kt exists under API source."""
    candidate_dir = api.mt_abs_path()
    if not candidate_dir.exists():
        return False
    for ext in (".java", ".kt"):
        if any(candidate_dir.rglob(f"{OPERATION_TEST_CLASS}{ext}")):
            return True
    return False

def _start_operation_test_background(
    op,
    *,
    port_pattern: str,
    startup_timeout: int = 120,
    with_jacoco: bool = False,
    jacoco_file_suffix: str = "",
) -> tuple[subprocess.Popen, int]:
    """
    Launch `mvn OperationTest` and parse the server port from console logs.

    Parameters
    ----------
    op : OperationConfig
        Operation configuration object defining the API module to run.
    port_pattern : str
        Regular expression with a single capturing group for the port number.
        Example: r"Tomcat started on port\\(s\\): (\\d+)"
    startup_timeout : int, optional
        Maximum seconds to wait for port detection.

    Returns
    -------
    (proc, port) : Tuple[subprocess.Popen, int]
        The running OperationTest process and the detected port number.

    Raises
    ------
    click.ClickException
        If the port is not detected or process exits prematurely.
    """
    if not port_pattern:
        raise click.ClickException("A port regex must be provided via --port-regex.")

    api = op.api

    if api.is_ind:
        click.echo(f"[OperationTest] Skipping IND API '{api.name}' (no local module).")
        return None, -1

    if not _operation_test_exists(api):
        raise click.ClickException(
            f"[OperationTest] Warning: {OPERATION_TEST_CLASS} not found under {api.mt_abs_path()}. "
            "Continuing without launching the service."
        )
        

    env = make_java_env(api.jdk_version.home)
    cmd = [
        api.build_tool.value,
        "-q",
        "-pl", api.maven_module_selector(),
        "-am", "test",
        "-DfailIfNoTests=false",
        "-Dsurefire.failIfNoSpecifiedTests=false",
        f"-Dtest={OPERATION_TEST_CLASS}",
    ]

    if with_jacoco:
        if not JACOCO_AGENT_PATH.exists():
            raise click.ClickException(f"JaCoCo agent jar not found: {JACOCO_AGENT_PATH}")
        
        api_module_name = api.maven_module_selector().split('/')[-1]
        destfile = api.mt_abs_path() / "target" / f"{jacoco_file_suffix}_jacoco.exec"
        destfile.parent.mkdir(parents=True, exist_ok=True)
        if destfile.exists():
            click.echo(f"[OperationTest] Removing existing JaCoCo exec: {destfile}")
            destfile.unlink()
        argline_value = f"-javaagent:{JACOCO_AGENT_PATH}=destfile={destfile},append=true"
        cmd.append(f'-DargLine={argline_value}')

    work_dir = api.work_dir()
    click.echo(f"[SUT] Launching OperationTest in {work_dir}: {' '.join(cmd)}")

    try:
        pattern = re.compile(port_pattern)
    except re.error as e:
        raise click.ClickException(f"Invalid port regex: {e}")

    proc = subprocess.Popen(
        cmd,
        cwd=str(work_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
        start_new_session=True,
    )

    found_port: Optional[int] = None
    found_evt = threading.Event()
    stop_reader_evt = threading.Event()

    def _reader_and_drain():
        """
        Continuously read and "drain" SUT output to avoid stdout pipe filling up causing SUT blocking (backpressure).
        After port is matched, continue reading but no longer print (optionally write to file).
        """
        nonlocal found_port
        try:
            for line in iter(proc.stdout.readline, ''):
                # Optional: mirror logs only when port not yet found, silent drain after found
                if not found_evt.is_set():
                    m = pattern.search(line)
                    if m:
                        try:
                            found_port = int(m.group(1))
                        except Exception:
                            # Fallback: don't let type parsing exception block
                            pass
                        click.secho(f"[SUT] ✅ Detected port: {found_port}", fg="green")
                        found_evt.set()
                        # FIX: don't return, continue "draining" to avoid stdout backpressure blocking
                        # If you want to write subsequent logs to file, open file handle here and write
                        # with open(f"/tmp/operationtest_{api.name}.log", "a") as lf: ...
                        continue
                # Default: silently discard; can print for debugging:
                # sys.stdout.write(line)
                # sys.stdout.flush()
                if stop_reader_evt.is_set():
                    break
        finally:
            try:
                if proc.stdout:
                    proc.stdout.close()
            except Exception:
                pass


    # FIX: change read thread to continuous drain, avoid backpressure from original implementation exiting after port match
    t = threading.Thread(target=_reader_and_drain, daemon=True)  # daemon=True: don't block main process exit
    t.start()

    # FIX: fine-grained waiting, replacing original 5s polling with maximum 5s extra delay
    deadline = time.time() + startup_timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            # ISSUE: original implementation threw error directly when subprocess exited early, without cleaning resources
            # FIX: give a hint before throwing error here
            raise click.ClickException(f"[SUT] Process exited early (exit={proc.returncode}).")
        if found_evt.is_set():
            # Return when port is found (keep drain thread running to prevent backpressure)
            return proc, found_port
        time.sleep(0.2)

    # Timeout: graceful termination -> force kill; ensure no zombie processes
    click.secho(f"[SUT] ⏱️ No port detected within {startup_timeout}s. Stopping SUT...", fg="yellow")
    try:
        # FIX: prioritize group termination to ensure Maven subprocesses are also terminated
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            proc.kill()
        proc.wait()

    # FIX: notify read thread to exit and try to finish up
    stop_reader_evt.set()
    try:
        if proc.stdout:
            proc.stdout.close()
    except Exception:
        pass
    # daemon thread doesn't force join, but can give a short timeout
    t.join(timeout=2)

    raise click.ClickException(f"[SUT] No port detected within {startup_timeout}s.")

def _invoke_operation_test_with_jacoco(*, op: OperationConfig, file_prefix: str, dry_run: bool) -> None:
    """Run mvn test -Dtest=OperationTest and inject JaCoCo agent via -DargLine."""
    api = op.api
    if api.is_ind:
        click.echo(f"[OperationTest] Skipping IND API '{api.name}' (no local module).")
        return

    if not _operation_test_exists(api):
        click.echo(
            f"[OperationTest] Warning: {OPERATION_TEST_CLASS} not found under {api.mt_abs_path()}. "
            "Continuing without launching the service."
        )
        return

    env = make_java_env(api.jdk_version.home)
    work_dir = Path(api.work_dir())

    if not JACOCO_AGENT_PATH.exists():
        raise click.ClickException(f"JaCoCo agent jar not found: {JACOCO_AGENT_PATH}")

    # Equivalent to destfile=$(pwd)/target/jacoco.exec when cwd=work_dir
    api_module_name = api.maven_module_selector().split('/')[-1]
    destfile = work_dir / "mt" / api_module_name / "jacoco" / f"{file_prefix}_jacoco.exec"
    destfile.parent.mkdir(parents=True, exist_ok=True)

    if destfile.exists():
        click.echo(f"[OperationTest] Removing existing JaCoCo exec: {destfile}")
        destfile.unlink()

    # Match your working CLI exactly: -DargLine=" -javaagent:...=destfile=...,append=true"
    # Note: do NOT add extra quoting here; subprocess list args is safest.
    argline_value = (
        f"-javaagent:{JACOCO_AGENT_PATH}=destfile={destfile},append=true"
    )

    cmd = [
        api.build_tool.value,  # usually "mvn"
        "-pl",
        api.maven_module_selector(),
        "-am",
        "test",
        "-DfailIfNoTests=false",
        "-Dsurefire.failIfNoSpecifiedTests=false",
        f"-Dtest={OPERATION_TEST_CLASS}",
        f'-DargLine={argline_value}',
    ]

    click.echo(f"[OperationTest] JaCoCo exec => {destfile}")
    click.echo(f"[OperationTest] Running in {work_dir}: {' '.join(cmd)}")

    if dry_run:
        click.echo("[OperationTest] Dry-run mode, command not executed.")
        return

    try:
        subprocess.run(cmd, check=True, cwd=str(work_dir), env=env)
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(
            f"Failed to execute OperationTest (+JaCoCo) for API '{api.name}'."
        ) from exc

def _invoke_operation_test(op: OperationConfig, dry_run: bool) -> None:
    """Run mvn test -Dtest=OperationTest for the given API operation."""
    api = op.api
    if api.is_ind:
        click.echo(f"[OperationTest] Skipping IND API '{api.name}' (no local module).")
        return

    if not _operation_test_exists(api):
        click.echo(
            f"[OperationTest] Warning: {OPERATION_TEST_CLASS} not found under {api.mt_abs_path()}. "
            "Continuing without launching the service."
        )
        return

    env = make_java_env(api.jdk_version.home)
    cmd = [
        api.build_tool.value,
        "-pl",
        api.maven_module_selector(),
        "-am",
        "test",
        "-DfailIfNoTests=false",
        "-Dsurefire.failIfNoSpecifiedTests=false",
        f"-Dtest={OPERATION_TEST_CLASS}",
    ]

    work_dir = api.work_dir()
    click.echo(f"[OperationTest] Running in {work_dir}: {' '.join(cmd)}")

    if dry_run:
        click.echo("[OperationTest] Dry-run mode, command not executed.")
        return

    try:
        subprocess.run(cmd, check=True, cwd=str(work_dir), env=env)
    except subprocess.CalledProcessError as exc:
        raise click.ClickException(
            f"Failed to execute OperationTest for API '{api.name}'."
        ) from exc

    

def api_op_options(func):
    """Decorator to add shared CLI options (--api, --operation)."""
    func = click.option('--operation', 'operation_id', required=True, type=str,
                        help='Operation id defined for the API.')(func)
    func = click.option('--api', 'api_name', required=True, type=str,
                        help='API name defined in op_configs.py.')(func)
    return func


def run_evomaster_blackbox(
        *,
        oas: str,
        # endpoint: str,
        host_url: str,
        schema_oracles: bool = True,
        security: bool = True,
        output_dir: str,
        output_format: str = "JAVA_JUNIT_5",
        problem_type: str = "REST",
        max_evaluations: int,  # << use evaluation-count budget
        rate_per_minute: int = 120,
        headers: Optional[Iterable[str]] = None,  # ["Authorization: Bearer TOKEN", ...] (max 3)
        seed: int = 42,
        config_file: Optional[str] = None,  # em.yaml for declarative auth (cookies/tokens)
        advanced_blackbox_coverage: bool = True,
        max_assertion_for_data_in_collection: int = -1,
        basic_assertions: bool,
        output_file_prefix: str,  # com.example.MyTest
        dry_run: bool = True,
) -> int:
    """
    Run EvoMaster in black-box mode for a single API operation.

    This wrapper exposes two categories of EvoMaster parameters to control both the core experimental setup and optional advanced behaviors.

    ──────────────────────────────────────────────
    1. Experimental / Required parameters
    ──────────────────────────────────────────────
    These are mandatory for every black-box experiment and define what to test,
    where to output results, and how to reproduce runs.

    - --blackBox
        Enables EvoMaster’s black-box mode (no driver, pure HTTP-based exploration).

    - --problemType
        The type of SUT we want to generate tests for, i.e., REST

    - --bbSwaggerUrl
        Path or URL to the OpenAPI / Swagger specification used to guide request generation.

    - --bbTargetUrl
        Base URL of the running System Under Test (SUT) — the REST endpoint root.

    - --outputFolder
        Directory where EvoMaster writes generated test cases, logs, and temporary data.

    - --outputFormat
        Target language/framework for generated tests, e.g. `JAVA_JUNIT_5`, `PYTHON_UNITTEST`, `JS_JEST`.

    - --configFile
        Optional path to an `em.yaml` configuration file that may include authentication
        declarations (e.g., loginEndpointAuth → cookies or token extraction).

    - --ratePerMinute
        Maximum number of HTTP requests EvoMaster can send per minute to avoid rate-limit
        or quota violations on the target API.

    - --header0 / --header1 / --header2
        Static HTTP headers (e.g., Authorization or API keys) to include with all requests.
        Only up to three headers are supported directly via CLI flags. This should be provided in the form `name:value`

    - --seed
        Random seed to ensure deterministic search and reproducible experiments.

    ──────────────────────────────────────────────
    2. Configurable parameters
    ──────────────────────────────────────────────
    These control exploration depth, assertion scope, and coverage heuristics.
    They are optional but useful for tuning evaluation and validation behavior.

    - --advancedBlackBoxCoverage
        Enables additional heuristics and structural coverage objectives beyond
        basic endpoint reachability (default: true).

    - --maxEvaluations
        Maximum number of fitness evaluations (iterations) during the search.
        This acts as an iteration-based stopping criterion, as opposed to --maxTime.

    - --maxAssertionForDataInCollection
        Upper limit on how many assertions EvoMaster will collect per test during data-collection phases.
        Note that zero means that only the size of the collection will be asserted.
        A negative value means all data in the collection will be asserted (i.e., no limit).
        Default value: 3.

    - --security
        Enables built-in security test generation (SQLi, XSS, SSRF, etc.) after functional tests.

    - --schemaOracles
        Activates response validation based on the OpenAPI schema. When enabled,
        EvoMaster automatically asserts response type, status codes, and field structure.

    - --enableBasicAssertions
        Activates regression style test assertions in the final test suites.

    ──────────────────────────────────────────────
    All option names and semantics correspond exactly to the entries defined
    in EvoMaster’s official `options.md`. For any new parameter additions,
    always verify naming and type against that file to avoid mismatches.

    Returns:
        Exit code from the EvoMaster process (0 means success). In dry-run, returns 0.
    """

    # -------- Helpers ---------------------------------------------------------
    def _to_bool_str(v: bool) -> str:
        return "true" if bool(v) else "false"

    def _to_oas_url(s: str) -> str:
        if s.startswith(("http://", "https://", "file://")):
            return s
        p = Path(s).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"OAS not found: {p}")
        return p.as_uri()

    # -------- Validate critical inputs ---------------------------------------
    if rate_per_minute <= 0:
        raise ValueError("`rate_per_minute` must be a positive integer.")
    if max_evaluations not in (10, 100, 1000, 10_000):
        raise ValueError("`max_evaluations` must be one of 100, 1000.")
    if max_assertion_for_data_in_collection not in (-1, 0, 3):
        raise ValueError("`max_assertion_for_data_in_collection` must be one of -1, 0, 3.")

    # -------- Resolve EvoMaster JAR ------------------------------------------
    if EM_JAR is None or not EM_JAR.is_file():
        hint = "Set a valid path in global EM_JAR or environment variable EVOMASTER_JAR"
        raise FileNotFoundError(f"EvoMaster jar not found. {hint}.")

    # -------- OAS URL & output directory -------------------------------------
    oas_url = _to_oas_url(oas)
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # -------- Build command ---------------------------------------------------
    java_cmd = Path(JdkVersion.JAVA_17.value) / "bin" / "java"
    cmd = [str(java_cmd)]
    # jvm_opts = ["-Dhttp.proxySet=true", '-Dhttp.nonProxyHosts=', "-Dhttp.proxyHost=127.0.0.1", "-Dhttp.proxyPort=8080", "-Dhttps.proxyHost=127.0.0.1", "-Dhttps.proxyPort=8080"]
    jvm_opts = []
    if jvm_opts:
        cmd.extend(list(jvm_opts))

    cmd.extend([
        "-jar", str(EM_JAR),
        "--blackBox", "true",
        "--problemType", problem_type,
        "--bbSwaggerUrl", oas_url,
        "--outputFormat", output_format,
        "--outputFolder", str(out_dir),
        "--outputFilePrefix", output_file_prefix,
        "--ratePerMinute", str(rate_per_minute),
        "--schemaOracles", _to_bool_str(schema_oracles),
        "--security", _to_bool_str(security),
        "--seed", str(seed),
        "--stoppingCriterion", "ACTION_EVALUATIONS",
        "--maxEvaluations", str(max_evaluations),
        "--advancedBlackBoxCoverage", _to_bool_str(advanced_blackbox_coverage),
        "--maxAssertionForDataInCollection", str(max_assertion_for_data_in_collection),
        "--showProgress", "true"
    ])

    if basic_assertions:
        cmd.extend(["--enableBasicAssertions", "true"])
    else:
        cmd.extend(["--enableBasicAssertions", "false"])

    if host_url:
        cmd.extend(["--bbTargetUrl", host_url,])

    # Optional: external em.yaml for declarative auth (login → cookies/tokens)
    if config_file:
        cfg_path = Path(config_file).expanduser().resolve()
        if not cfg_path.is_file():
            raise FileNotFoundError(f"`config_file` not found: {cfg_path}")
        cmd.extend(["--configPath", str(cfg_path)])

    # Optional: static headers (only for long-lived tokens/API keys)
    if headers:
        hdrs = list(headers)[:3]
        for i, h in enumerate(hdrs):
            if ":" not in h:
                raise ValueError(f"Header must be in 'Name:Value' format, got: {h!r}")
            cmd.extend([f"--header{i}", h])

    # -------- Pretty-print reproducible command ------------------------------
    printable = " ".join(shlex.quote(c) for c in cmd)
    print(">>> EvoMaster command:")
    print(printable, flush=True)

    if dry_run:
        print(">>> Dry-run: command not executed.")
        return 0

    # -------- Execute and stream output --------------------------------------
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            env=os.environ.copy(),
        )
    except Exception as e:
        print(f">>> Failed to start EvoMaster: {e}", flush=True)
        return 1

    for line in iter(proc.stdout.readline, ''):
        sys.stdout.write(line)
        sys.stdout.flush()

    proc.stdout.close()
    rc = proc.wait()
    print(f"\n>>> EvoMaster exited with code: {rc}", flush=True)
    return rc


@click.group(help="CLI for OperationTest (mvn) and EvoMaster black-box execution.")
def cli():
    pass


# =========================================================================
# Command 1: OperationTest
# =========================================================================
@cli.command(name='op-test', help='Run mvn OperationTest for a configured API operation.')
@api_op_options
@click.option('--dry-run', is_flag=True, help='Print command without executing.')
def op_test(api_name: str, operation_id: str, dry_run: bool) -> None:
    """Run the Maven OperationTest class."""
    op_config = _resolve_operation_config(api_name, operation_id)
    endpoint = f"{op_config.http_method}:{op_config.operation_path}"
    oas = op_config.resolved_oas()

    click.echo(f"🧪 OperationTest for API='{op_config.api.name}' OP='{op_config.id}'")
    click.echo(f"   endpoint={endpoint}\n   oas={oas}")

    _invoke_operation_test(op_config, dry_run=dry_run)
    click.secho("✅ OperationTest finished (or printed command with --dry-run).", fg="green")


def make_em_package_name(
        api_name: str,
        operation_id: str,
        *,
        schema_oracles: bool,
        security: bool,
        advanced_blackbox_coverage: bool,
        max_assertion_for_data_in_collection: int,
        max_evaluations: int,
) -> str:
    """
    Construct EvoMaster output package name and corresponding output directory.

    Package name encodes key experimental parameters for reproducibility:
        {adv|noadv}.{assertN|assertsize|assertall}.eval{N}.{sec|nosec}.{schema|noschema}

    Example:
        adv.assert3.eval5000.sec.schema
        noadv.assertall.eval2000.nosec.noschema

    Returns:
        (package_name, output_dir: Path)
    """

    def _pkg_bool(flag: bool, yes: str, no: str) -> str:
        return yes if flag else no

    adv_tag = _pkg_bool(advanced_blackbox_coverage, "adv", "noadv")

    if max_assertion_for_data_in_collection < 0:
        assert_tag = "assertall"
    elif max_assertion_for_data_in_collection == 0:
        assert_tag = "assertsize"
    else:
        assert_tag = f"assert{max_assertion_for_data_in_collection}"

    eval_tag = f"eval{max_evaluations}"
    sec_tag = _pkg_bool(security, "security", "nosecurity")
    schema_tag = _pkg_bool(schema_oracles, "schema", "noschema")
    api_name = api_name if api_name != "YouTube-getVideos" else "YouTube"
    return ".".join([api_name, operation_id, adv_tag, assert_tag, eval_tag, sec_tag, schema_tag, "Original"])


# =========================================================================
# Command 2: EvoMaster Black-Box  (UPDATED to match latest run_evomaster_blackbox)
# =========================================================================
@cli.command(name='evomaster', help='Launch EvoMaster black-box for a configured API operation.')
@api_op_options
@click.option('--host-url', type=str, required=True,
              help='Base URL of the target API (e.g., http://localhost:8080).')
@click.option('--schema-oracles/--no-schema-oracles', default=True, show_default=True,
              help='Enable/disable schema oracles.')
@click.option('--security/--no-security', default=True, show_default=True,
              help='Enable/disable security testing.')
@click.option('--max-evaluations', default=10000, show_default=True, type=int,
              help='Maximum number of search evaluations (iteration-based stopping).')
@click.option('--rate-per-minute', default=120, show_default=True, type=int,
              help='Request rate limit per minute.')
@click.option('--headers', multiple=True,
              help="Optional headers, e.g., 'Authorization: Bearer TOKEN'. Up to 3 are used.")
@click.option('--config-file', type=click.Path(exists=True),
              help='Optional em.yaml configuration file.')
@click.option('--advanced-blackbox-coverage/--no-advanced-blackbox-coverage',
              default=True, show_default=True,
              help='Enable additional black-box coverage heuristics.')
@click.option('--max-assertion-for-data-in-collection', default=3, show_default=True, type=int,
              help='Limit assertions collected per test during data-collection phases. 0=size-only, negative=unlimited.')
@click.option('--dry-run', is_flag=True, help='Print command without executing.')
def evomaster_cmd(
        *,
        api_name: str,
        operation_id: str,
        host_url: str,
        schema_oracles: bool = True,
        security: bool = True,
        max_evaluations: int,
        rate_per_minute: int,
        headers: Iterable[str] | None,
        config_file: str | None,
        advanced_blackbox_coverage: bool = True,
        max_assertion_for_data_in_collection: int = -1,
        basic_assertions: bool,
        dry_run: bool,
) -> None:
    """Run EvoMaster black-box mode with options aligned to run_evomaster_blackbox()."""
    op_config = _resolve_operation_config(api_name, operation_id)

    endpoint = f"{op_config.http_method}:{op_config.operation_path}"
    oas = op_config.resolved_oas()

    package_name = make_em_package_name(api_name,
                                        operation_id,
                                        schema_oracles=schema_oracles,
                                        advanced_blackbox_coverage=advanced_blackbox_coverage,
                                        security=security,
                                        max_evaluations=max_evaluations,
                                        max_assertion_for_data_in_collection=max_assertion_for_data_in_collection)

    output_dir = WITH_BASIC_ASSERTIONS_OUTPUT_ROOT if basic_assertions else WITHOUT_BASIC_ASSERTIONS_OUTPUT_ROOT

    click.echo(f"🚀 EvoMaster for API='{op_config.api.name}' OP='{op_config.id}'")
    click.echo(f"   endpoint={endpoint}\n   oas={oas}\n   host={host_url}\n   rpm={rate_per_minute}")
    click.echo(f"   output_dir={output_dir}")
    click.echo(f"   package_name={package_name}")
    click.echo(f"   options: schema_oracles={schema_oracles}, security={security}, "
               f"max_evaluations={max_evaluations}, "
               f"advancedBBCov={advanced_blackbox_coverage}, "
               f"maxAssertInColl={max_assertion_for_data_in_collection}")

    rc = run_evomaster_blackbox(
        oas=oas,
        host_url=host_url,
        schema_oracles=schema_oracles,
        security=security,
        output_dir=str(output_dir),
        output_format=FIXED_OUTPUT_FORMAT,
        output_file_prefix=package_name,
        problem_type=FIXED_PROBLEM_TYPE,
        max_evaluations=max_evaluations,
        rate_per_minute=rate_per_minute,
        headers=headers,
        seed=FIXED_SEED,
        config_file=config_file,
        advanced_blackbox_coverage=advanced_blackbox_coverage,
        max_assertion_for_data_in_collection=max_assertion_for_data_in_collection,
        basic_assertions=basic_assertions,
        dry_run=dry_run,
    )

    if rc == 0:
        click.secho("✅ EvoMaster execution finished successfully.", fg="green")
    else:
        click.secho(f"❌ EvoMaster exited with code {rc}", fg="red")
    # raise SystemExit(rc)

def get_token(_api: ApiConfig):
    if _api.name == "ScoutAPI":
        return ["Authorization:ApiKey administrator"]
    elif _api.name == "Market":
        return ["Authorization:Basic dXNlcjJAeWFuZGV4LnJ1Onl1cmlkb2xnb3J1a2k="]
    elif _api.name == "Deutschebahn":
        return ["DB-Api-Key:51e998a9994f3b6d8352af3dcaa284eb", "DB-Client-ID:ccace9465566efff0d12cb3577b82fe0"]
    elif _api.name == "Foursquare":
        return ["Authorization:Bearer XE51J0AKCM0IIDRYFXAGWRQTPOTOR1J414KZPSFGAZ0QYVXQ"]
    elif _api.name == "Stripe":
        return ["Authorization:Bearer sk_test_51SZb9aFp2AHz8iajQSy5t7xOhu59Z10TCzHc8p8sqGVod04osKiqOodKtKT0ALsZpYaJ3N544esaxS8M9VL8R5oX00NUvJDUo1"]
    # elif _api.name == "Yelp":
    #     return ["Authorization:Bearer _r_qNWVkIo-Y2y7drBhlWXd8EB8kmHk0B6_idrjHkdf_yAtvWLHb3OvPsx7-TJ70OJUtvAHbbsBXaoNkaMI8fDr-flxaPBJZyz-SPlpLsIDNRcBmMkLEwIH_B5suaXYx"]
    else:
        return None

    
CONFIG_DIR = SCRIPT_DIR / "evo" / "configs"
def get_ind_config(_api: ApiConfig):
    if _api.name == "AmadeusHotel":
        return CONFIG_DIR / "amadeus-em.yaml"
    elif _api.name == "DHL":
        return CONFIG_DIR / "dhl-em.yaml"
    elif _api.name == "Yelp":
        return CONFIG_DIR / "yelp-em.yaml"
    elif _api.name == "YouTube-getVideos":
        return CONFIG_DIR / "youtube-em.yaml"
    return None

def get_rate_limit(_api: ApiConfig):
    if _api.is_ind:
        if _api.name == "AmadeusHotel":
            return 100
        elif _api.name == "Deutschebahn":
            return 100
        elif _api.name == "DHL":
            return 20
        elif _api.name == "FDIC":
            return 30
        elif _api.name == "Foursquare":
            return 20
        elif _api.name == "iTunes":
            return 10
        elif _api.name == "Ohsome":
            return 10
        elif _api.name == "Stripe":
            return 60
        elif _api.name == "Yelp":
            return 10
        elif _api.name == "YouTube":
            return 20
        else: 
            raise ValueError(f"NOT IMPLEMENTED FOR {_api.name}")
    else:
        return 500

if __name__ == '__main__':
    # cli()
    # for _api, _op_list in OPS_MAP.items():
    #     if _api.is_ind:
    #         continue
    #     if _api.name != "UserManagement":
    #         continue
    #     for _op in _op_list:
    #         _api_proc, port = _start_operation_test_background(_op, port_pattern=r"API is started on port: (\d+)", startup_timeout=6000)
    #         evomaster_cmd.callback(
    #             api_name=_api.name,
    #             operation_id=_op.id,
    #             host_url=f"http://localhost:{port}",
    #             # schema_oracles=True,
    #             # security=True,
    #             max_evaluations=10_000,
    #             rate_per_minute=500,
    #             headers=get_token(_api),
    #             config_file=None,
    #             # advanced_blackbox_coverage=True,
    #             # max_assertion_for_data_in_collection=-1,
    #             basic_assertions=False,
    #             dry_run=False
    #         )
    #         _api_proc.terminate()

    #         _api_proc, port = _start_operation_test_background(_op, port_pattern=r"API is started on port: (\d+)", startup_timeout=6000)
    #         evomaster_cmd.callback(
    #             api_name=_api.name,
    #             operation_id=_op.id,
    #             host_url=f"http://localhost:{port}",
    #             # schema_oracles=True,
    #             # security=True,
    #             max_evaluations=10_000,
    #             rate_per_minute=500,
    #             headers=get_token(_api),
    #             config_file=None,
    #             # advanced_blackbox_coverage=True,
    #             # max_assertion_for_data_in_collection=-1,
    #             basic_assertions=True,
    #             dry_run=False
    #         )
    #         _api_proc.terminate()

    for _api, _op_list in OPS_MAP.items():
        if not _api.is_ind:
            continue
        if _api.name not in ("Yelp"):
            continue
        for _op in _op_list:
            evomaster_cmd.callback(
                    api_name=_api.name,
                    operation_id=_op.id,
                    host_url=None,
                    # schema_oracles=True,
                    # security=True,
                    max_evaluations=1000,
                    rate_per_minute=get_rate_limit(_api),
                    headers=get_token(_api),
                    config_file=get_ind_config(_api),
                    # advanced_blackbox_coverage=True,
                    # max_assertion_for_data_in_collection=-1,
                    basic_assertions=False,
                    dry_run=False
                )
            # evomaster_cmd.callback(
            #     api_name=_api.name,
            #     operation_id=_op.id,
            #     host_url=None,
            #     # schema_oracles=True,
            #     # security=True,
            #     max_evaluations=1000,
            #     rate_per_minute=get_rate_limit(_api),
            #     headers=get_token(_api),
            #     config_file=get_ind_config(_api),
            #     # advanced_blackbox_coverage=True,
            #     # max_assertion_for_data_in_collection=-1,
            #     basic_assertions=True,
            #     dry_run=True
            # )
    
    # for _api, _op_list in OPS_MAP.items():
    #
    #     for op in _op_list:
    #         _invoke_operation_test_with_jacoco(op=op, file_prefix="emon", dry_run=True)