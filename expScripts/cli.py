# cli.py
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict

import click

from _email_sender import EmailSender
from op_configs import OPS_MAP, ApiConfig
from runner import run_preparation_only, run_endpoint_test_only, run_all

# Log initialization (keeping your original settings)
SCRIPT_DIR = Path(__file__).parent.resolve()
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = SCRIPT_DIR / "logs" / f"script_{timestamp}.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
fh = logging.FileHandler(str(LOG_FILE), mode="a", encoding="utf-8")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"))
logging.getLogger().addHandler(fh)
logger = logging.getLogger(__name__)


def list_available_configs():
    ops_map: Dict[ApiConfig, list] = OPS_MAP
    print("Available API Configurations:")
    print("=" * 50)

    for api, operations in ops_map.items():
        print(f"\nAPI: {api.name}")
        print(f"  JDK Version: {api.jdk_version.name}")
        print(f"  Build Tool: {api.build_tool.name}")
        print(f"  Module: {api.module_name}")
        print(f"  Preparation Class: {api.preparation_class}")
        print(f"  Endpoint Test Class: {api.endpoint_test_class}")
        print(f"  Operations:")
        for op in ops_map.get(api, []):
            print(f"    - {op.http_method} {op.operation_path}")
            print(f"      OAS File: {op.oas}")
            print(f"      PICT Model: {op.pict_model_file}")
            if op.csv_mapper:         print(f"      CSV Mapper: {op.csv_mapper}")
            if op.remove_json_paths:  print(f"      Remove JSON Paths: {op.remove_json_paths}")
            if op.remove_json_nodes:  print(f"      Remove JSON Nodes: {op.remove_json_nodes}")
            if op.mvn_profile:        print(f"      Maven Profile: {op.mvn_profile}")


def _build_sender_from_click(*, email: bool, email_on_failure: bool, email_on_start: bool, email_on_results: bool) -> EmailSender:
    return EmailSender(
        enabled=email,
        on_failure=email_on_failure,
        on_start=email_on_start,
        on_results=email_on_results,
    )


def _parse_multi(values):
    if not values:
        return None
    out = []
    for v in values:
        out.extend([x.strip() for x in str(v).split(",") if x.strip()])
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq or None


def email_feature_flags(fn):
    fn = click.option("--no-email-on-failure", is_flag=True, default=False, help="Do NOT send failure emails")(fn)
    fn = click.option("--email-on-results", is_flag=True, default=False, help="Enable results email (attachments)")(fn)
    fn = click.option("--email-on-start", is_flag=True, default=False, help="Enable start notification email")(fn)
    fn = click.option("--no-email", "email", is_flag=True, flag_value=False, default=False, help="Disable all emails")(fn)
    fn = click.option("--email", "email", is_flag=True, flag_value=True, default=True, help="Enable emails (default on; only failure emails active unless toggled)")(fn)
    return fn


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """If no subcommand is provided, it prints the available configurations."""
    if ctx.invoked_subcommand is None:
        list_available_configs()


@cli.command("list-configs")
def list_configs_cmd():
    list_available_configs()


@email_feature_flags
@cli.command("preparation")
@click.option("--api", "api_filter", help="API name filter")
@click.option("--op-id", "op_filter", help="Operation id filter (e.g., postUsers)")
def preparation_cmd(api_filter, op_filter, email, email_on_start, email_on_results, no_email_on_failure):
    sender = _build_sender_from_click(
        email=email,
        email_on_failure=not no_email_on_failure,
        email_on_start=email_on_start,
        email_on_results=email_on_results,
    )
    ops_map: Dict[ApiConfig, list] = OPS_MAP
    logger.info("Running preparation tests only")
    run_preparation_only(ops_map, api_filter=api_filter, op_filter=op_filter, email_sender=sender)


@email_feature_flags
@cli.command("endpoint")
@click.option("--api", "api_filter", help="API name filter")
@click.option("--op-id", "op_filter", help="Operation id filter (e.g., postUsers)")
@click.option("--level", multiple=True, help="Assertion level filter; repeat or comma-separate")
@click.option("--mode", multiple=True, help="Test mode filter; repeat or comma-separate")
@click.option("--strength", multiple=True, help="Covering strength filter; repeat or comma-separate")
def endpoint_cmd(api_filter, op_filter, level, mode, strength, email, email_on_start, email_on_results, no_email_on_failure):
    sender = _build_sender_from_click(
        email=email,
        email_on_failure=not no_email_on_failure,
        email_on_start=email_on_start,
        email_on_results=email_on_results,
    )
    ops_map: Dict[ApiConfig, list] = OPS_MAP
    logger.info("Running endpoint tests only")
    run_endpoint_test_only(
        ops_map,
        api_filter=api_filter,
        op_filter=op_filter,
        level_filter=_parse_multi(level),
        mode_filter=_parse_multi(mode),
        strength_filter=_parse_multi(strength),
        email_sender=sender
    )


@email_feature_flags
@cli.command("run-all")
@click.option("--api", "api_filter", help="API name filter")
@click.option("--op-id", "op_filter", help="Operation id filter (e.g., postUsers)")
@click.option("--level", multiple=True, help="Assertion level filter; repeat or comma-separate")
@click.option("--mode", multiple=True, help="Test mode filter; repeat or comma-separate")
@click.option("--strength", multiple=True, help="Covering strength filter; repeat or comma-separate")
def run_all_cmd(api_filter, op_filter, level, mode, strength, email, email_on_start, email_on_results, no_email_on_failure):
    sender = _build_sender_from_click(
        email=email,
        email_on_failure=not no_email_on_failure,
        email_on_start=email_on_start,
        email_on_results=email_on_results,
    )
    ops_map: Dict[ApiConfig, list] = OPS_MAP
    logger.info("Running both preparation and endpoint tests")
    run_all(
        ops_map,
        api_filter=api_filter,
        op_filter=op_filter,
        level_filter=_parse_multi(level),
        mode_filter=_parse_multi(mode),
        strength_filter=_parse_multi(strength),
        email_sender=sender
    )


@cli.command("clean-postman")
@click.option(
    "--api", "api_filter",
    multiple=True,
    help="API name filter (can be repeated: --api petStore --api catWatch)"
)
@click.option("--dry-run", is_flag=True, help="Only list directories; do not delete.")
def clean_postman_cmd(api_filter, dry_run: bool):
    """
    Delete all Postman workspace directories for the selected APIs.
    """
    ops_map: Dict[ApiConfig, list] = OPS_MAP

    matched: list[Path] = []
    for api, operations in ops_map.items():
        if api_filter and api.name not in api_filter:
            continue

        for p in api.mt_abs_path().rglob("agora/postman_workspace"):
            if not p.is_dir():
                continue

            matched.append(p)

    if not matched:
        logger.info("No postman workspace directories found%s.", f" for APIs {api_filter}" if api_filter else "")
        return

    logger.info("Found %d postman workspace directories:", len(matched))
    for p in matched:
        logger.info("  %s", p)

    if dry_run:
        logger.info("Dry run: no directories were deleted.")
        return

    # deleting
    removed = 0
    for p in matched:
        try:
            shutil.rmtree(p, ignore_errors=False)
            logger.info("Deleted: %s", p)
            removed += 1
        except Exception as e:
            logger.error("Failed to delete %s: %s", p, e)

    logger.info("Cleaned %d/%d postman workspace directories.", removed, len(matched))


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
