# runner.py
import logging
import shutil
from itertools import product
from pathlib import Path
from typing import Dict, List, Optional

from _email_sender import EmailSender
from exec_utils import make_java_env, run_command
from op_configs import (
    ROOT_DIR, JdkVersion, OperationConfig, ApiConfig, SCRIPT_DIR
)
from pitest_utils import append_pitest_results

TOOL_DIR = SCRIPT_DIR / "tools"
PM_AJ = TOOL_DIR / "PostmanAssertify.jar"
NEWMAN_JS_DIR = TOOL_DIR / "fail-only-fast-min.js"
logger = logging.getLogger(__name__)
_MISSING_ENDPOINT_NOTIFIED: set[str] = set()


def _endpoint_test_exists(api: ApiConfig) -> bool:
    test_class = api.endpoint_test_class.split(".")[-1]
    base = api.mt_abs_path()
    candidate_dirs = [
        base / "src" / "test" / "java",
    ]
    for directory in candidate_dirs:
        if not directory.exists():
            continue
        for ext in (".java", ".kt"):
            if any(directory.rglob(f"{test_class}{ext}")):
                return True
    return False


def _prepare(op: OperationConfig, email_sender: EmailSender) -> None:
    api = op.api
    if api.is_ind:
        logger.warning(
            "[Preparation] Skipping API=%s OP=%s because IND APIs have no preparation phase.",
            api.name, op.operation_path
        )
        return

    work_dir = api.work_dir()
    module_selector = api.maven_module_selector()

    logger.info("[Preparation] API=%s OP=%s", api.name, op.operation_path)

    env = make_java_env(api.jdk_version.home)
    cmd_parts = [
        api.build_tool.value, f"-pl {module_selector}", "-am", "test",
        f"-Dtest={api.preparation_class}",
        "-DfailIfNoTests=false",
        "-Dsurefire.failIfNoSpecifiedTests=false",
        f"-Dhttpmut.operationPath={op.operation_path}",
        f"-Dhttpmut.httpMethod={op.http_method}",
        f"-Dhttpmut.oas={op.resolved_oas()}",
        f"-Dhttpmut.pictModelFile={op.resolved_model()}",
        "-Dhttpmut.workingDir=httpmutator/",
        f"-Dhttpmut.java17Exec={Path(JdkVersion.JAVA_17.value) / 'bin' / 'java'}",
        f"-Dhttpmut.postmanAssertifyJar={PM_AJ.absolute()}",
        f"-Dhttpmut.newmanJsFile={NEWMAN_JS_DIR.absolute()}"
    ]
    if op.csv_mapper:        cmd_parts.append(f"-Dhttpmut.csvMapper={op.csv_mapper}")
    if op.remove_json_paths: cmd_parts.append(f"-Dhttpmut.removedJsonPaths={op.remove_json_paths}")
    if op.remove_json_nodes: cmd_parts.append(f"-Dhttpmut.removedJsonNodes={op.remove_json_nodes}")
    if op.remove_headers:    cmd_parts.append(f"-Dhttpmut.removedHeaderFields={op.remove_headers}")

    cmd = " ".join(cmd_parts)
    run_command(cmd, env, work_dir, email_sender)


def _endpoint_test(op: OperationConfig, level: str, mode: str, strength: str, email_sender: EmailSender) -> None:
    api = op.api
    is_white = mode.upper() == "WHITE"
    if api.is_ind and is_white:
        logger.warning(
            "[EndpointTest] Skipping WHITE mode for IND API=%s OP=%s",
            api.name, op.operation_path
        )
        return

    jdk_home = api.jdk_version.home if not is_white else JdkVersion.JAVA_11.home

    work_dir = api.work_dir()
    module_selector = api.maven_module_selector()

    endpoint_key = f"{api.name}:{api.endpoint_test_class}"
    if not _endpoint_test_exists(api):
        message = (
            f"Endpoint test class '{api.endpoint_test_class}' not found for API '{api.name}'. "
            f"Skipping endpoint execution."
        )
        logger.error(message)
        if endpoint_key not in _MISSING_ENDPOINT_NOTIFIED:
            if email_sender:
                try:
                    email_sender.send_failure_email("missing-endpoint-test", message)
                except Exception as exc:
                    logger.error("Failed to send failure email for missing endpoint test: %s", exc)
            _MISSING_ENDPOINT_NOTIFIED.add(endpoint_key)
        return

    logger.info("[EndpointTest] API=%s OP=%s LEVEL=%s MODE=%s STR=%s", api.name, op.operation_path, level, mode,
                strength)

    env = make_java_env(jdk_home)
    if is_white:
        operation_id = f"{op.http_method}{op.operation_path.replace('/', '').replace('{', '').replace('}', '')}"
        cmd_parts = [
            api.build_tool.value, "verify",
            f"-pl {module_selector}", "-am",
            "-DskipTests",
            f"-DoperationId={operation_id}"
        ]
    else:
        cmd_parts = [
            api.build_tool.value, "test",
            f"-pl {module_selector}", "-am",
            "-DfailIfNoTests=false",
            "-Dsurefire.failIfNoSpecifiedTests=false",
            f"-Dtest={api.endpoint_test_class}"
        ]

    cmd_parts += [
        f"-Dhttpmut.operationPath={op.operation_path}",
        f"-Dhttpmut.httpMethod={op.http_method}",
        f"-Dhttpmut.oas={op.resolved_oas()}",
        f"-Dhttpmut.level={level}",
        f"-Dhttpmut.testmode={mode}",
        f"-Dhttpmut.strength={strength}",
        f"-Dhttpmut.java17Exec={Path(JdkVersion.JAVA_17.value) / 'bin' / 'java'}",
        f"-Dhttpmut.postmanAssertifyJar={PM_AJ.absolute()}",
        f"-Dhttpmut.newmanJsFile={NEWMAN_JS_DIR.absolute()}",
        f"-Dhttpmut.workingDir=httpmutator/"
    ]
    if op.csv_mapper:        cmd_parts.append(f"-Dhttpmut.csvMapper={op.csv_mapper}")
    if op.remove_json_nodes: cmd_parts.append(f"-Dhttpmut.removedJsonNodes={op.remove_json_nodes}")
    if op.remove_json_paths: cmd_parts.append(f"-Dhttpmut.removedJsonPaths={op.remove_json_paths}")
    if op.remove_headers:    cmd_parts.append(f"-Dhttpmut.removedHeaderFields={op.remove_headers}")
    if is_white and op.mvn_profile: cmd_parts.append(f"-P{op.mvn_profile}")
    if level.upper() == "REGRESSION": cmd_parts.append("-Dhttpmut.exclusiveAssertions=true")

    cmd = " ".join(cmd_parts)
    timings, statistics = run_command(cmd, env, work_dir, email_sender, verbose=True, capture_pitest=is_white)

    if is_white and timings and statistics:
        append_pitest_results(api.name, op.id, mode, level, strength, timings, statistics)


def run_preparation_only(
        ops_map: Dict[ApiConfig, List[OperationConfig]],
        api_filter: Optional[str] = None,
        op_filter: Optional[str] = None,
        email_sender: Optional[EmailSender] = None
) -> None:
    for api, ops in ops_map.items():
        if api_filter and api.name != api_filter:
            continue
        for op in ops:
            if op_filter and op.id != op_filter:
                continue
            _prepare(op, email_sender)


def run_endpoint_test_only(
        ops_map: Dict[ApiConfig, List[OperationConfig]],
        api_filter: Optional[str] = None,
        op_filter: Optional[str] = None,
        level_filter: Optional[List[str]] = None,
        mode_filter: Optional[List[str]] = None,
        strength_filter: Optional[List[str]] = None,
        email_sender: Optional[EmailSender] = None
) -> None:
    all_levels = ["FIVE_XX", "OAS", "INVARIANT", "REGRESSION"]
    all_modes = ["BLACK", "BLACK_RANDOM", "WHITE"]
    all_strengths = ["ONE_WAY_REDUCED", "ONE_WAY", "TWO_WAY"]

    modes = mode_filter or all_modes
    levels = level_filter or all_levels
    strengths = strength_filter or all_strengths

    for api, ops in ops_map.items():
        if api_filter and api.name != api_filter:
            continue
        for op in ops:
            if op_filter and op.id != op_filter:
                continue
            for md, st, lvl in product(modes, strengths, levels):
                if md.upper() == "WHITE" and st.upper() != "TWO_WAY":
                    continue
                if api.is_ind and md.upper() == "WHITE":
                    logger.warning(
                        "[EndpointTest] Skipping WHITE mode for IND API=%s OP=%s",
                        api.name, op.operation_path
                    )
                    continue
                email_sender.send_notification(api.name, op.id, md, lvl, st)
                _endpoint_test(op, lvl, md, st, email_sender)


def run_all(
        ops_map: Dict[ApiConfig, List[OperationConfig]],
        api_filter: Optional[str] = None,
        op_filter: Optional[str] = None,
        level_filter: Optional[List[str]] = None,
        mode_filter: Optional[List[str]] = None,
        strength_filter: Optional[List[str]] = None,
        email_sender: Optional[EmailSender] = None
) -> None:
    """
        Iterate over all APIs and operations, optionally filtered.
        First run prepare phase (if enabled), then endpoint_test for each
        (level, mode, strength) combination.
        """
    run_preparation_only(ops_map, api_filter, op_filter, email_sender)

    run_endpoint_test_only(
        ops_map, api_filter, op_filter,
        level_filter, mode_filter, strength_filter, email_sender
    )
