import os
import shlex
import subprocess
import sys
from typing import Iterable, Optional
from runner import SCRIPT_DIR
from run_evomaster import _start_operation_test_background, _resolve_operation_config, get_token, get_rate_limit

OUTPUT_ROOT = SCRIPT_DIR / "schemathesis-unique-reports"

def run_schemathesis_cmd(
        api_name: str,
        operation_id: str,
        host_url: str,
        max_examples: int,
        rate_per_minute: int,
        headers: Optional[Iterable[str]],
        dry_run: bool,
) -> int:
    # -------- Helpers ---------------------------------------------------------
    def _to_bool_str(v: bool) -> str:
        return "true" if bool(v) else "false"

    op_config = _resolve_operation_config(api_name, operation_id)

    endpoint = f"{op_config.http_method}:{op_config.operation_path}"
    if op_config.api.name != "YouTube-getVideos":
        out_dir = OUTPUT_ROOT / op_config.api.name / op_config.id
    else:
        out_dir = OUTPUT_ROOT / "YouTube" / op_config.id
    out_dir.mkdir(parents=True, exist_ok=True)

    oas = op_config.resolved_oas()

    print(f"🚀 Schemathesis for API='{op_config.api.name}' OP='{op_config.id}'")
    print(f"   endpoint={endpoint}\n   oas={oas}\n   host={host_url}\n   rpm={rate_per_minute}")
    print(f"   output_dir={out_dir}")

    cmd = ["st", "run", oas]
    cmd.extend([
        "--checks", "all",
        "--continue-on-failure",
        "--rate-limit", f"{rate_per_minute}/m",
        "--report", "junit,har,vcr",
        "--report-dir", str(out_dir),
        "--output-truncate", "false",
        "--max-examples", str(max_examples),
        "--seed", "42",
        "--no-shrink",
        "--generation-unique-inputs",
        "--generation-deterministic",
        "--phases", "examples,fuzzing",
        "--request-timeout", "30",
    ])

    if api_name == "Foursquare":
        cmd.extend(["--header", "X-Places-Api-Version: 2025-06-17"])

    if host_url:
        cmd.extend(["--url", host_url,])

    if headers:
        for h in headers:
            if ":" not in h:
                raise ValueError(f"Header must be in 'Name:Value' format, got: {h!r}")
            cmd.extend(["--header", h])

    # -------- Pretty-print reproducible command ------------------------------
    printable = " ".join(shlex.quote(c) for c in cmd)
    print(">>> Schemathesis command:")
    print(printable, flush=True)

    if dry_run:
        print(">>> Dry-run: command not executed...")
        return 0
    
    env = os.environ.copy()
    if api_name in ("AmadeusHotel", "DHL", "Yelp", "YouTube"):
        env["SCHEMATHESIS_HOOKS"] = "sch_hooks"

    # -------- Execute and stream output --------------------------------------
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
            env=env,
            cwd=SCRIPT_DIR
        )
    except Exception as e:
        print(f">>> Failed to start Schemathesis: {e}", flush=True)
        return 1

    for line in iter(proc.stdout.readline, ''):
        sys.stdout.write(line)
        sys.stdout.flush()

    proc.stdout.close()
    rc = proc.wait()
    print(f"\n>>> Schemathesis exited with code: {rc}", flush=True)
    return rc

def get_base_path(api_name, op_name):
    if api_name == "LanguageTool" and op_name == "postCheck":
        return "/v2"
    elif api_name == "AmadeusHotel" and op_name == "getHotelOffers":
        return "/v3"
    elif api_name == "Ohsome" and op_name == "getElementsAggregation":
         return "/v1"
    elif api_name == "ScoutAPI" and op_name == "postActivities":
        return "/api"
    else:
        return ""
    
def get_ind_host_url(api_name):
    if api_name == "AmadeusHotel":
        return "https://test.api.amadeus.com/v3"
    elif api_name == "Deutschebahn":
        return "https://apis.deutschebahn.com/db-api-marketplace/apis/station-data/v2"
    elif api_name == "DHL":
        return "https://api.dhl.com"
    elif api_name == "FDIC":
        return "https://api.fdic.gov/banks"
    elif api_name == "Foursquare":
        return "https://places-api.foursquare.com/"
    elif api_name == "iTunes":
        return "https://itunes.apple.com"
    elif api_name == "Ohsome":
        return "https://api.ohsome.org/v1"
    elif api_name == "Stripe":
        return "https://api.stripe.com"
    elif api_name == "YouTube":
        return "https://youtube.googleapis.com"
    elif api_name == "Yelp":
        return "https://api.yelp.com/v3"
    else:
        raise ValueError(f"Unknown IND API: {api_name}")

if __name__ == "__main__":
    from op_configs import OPS_MAP
    # from jacoco_handler import generate_and_run_jacoco_report_for_operation
    # for _api, _op_list in OPS_MAP.items():
    #     if _api.is_ind:
    #         continue
    #     for _op in _op_list:
    #         _api_proc, port = _start_operation_test_background(_op, port_pattern=r"API is started on port: (\d+)", startup_timeout=6000, with_jacoco=True, jacoco_file_suffix="sch")
    #         run_schemathesis_cmd(
    #             api_name=_api.name,
    #             operation_id=_op.id,
    #             host_url=f"http://localhost:{port}{get_base_path(_api.name, _op.id)}",
    #             max_examples=10_000,
    #             rate_per_minute=500,
    #             headers=get_token(_api),
    #             dry_run=False
    #         )
    #         _api_proc.terminate()

    #         try:
    #             _api_proc.wait(timeout=30)
    #         except subprocess.TimeoutExpired:
    #             _api_proc.kill()
    #             _api_proc.wait()

    #         generate_and_run_jacoco_report_for_operation(
    #             op=_op,
    #             java_bin="java",
    #             report_root=_api.mt_abs_path() / "target",
    #             suffix="sch",
    #             dry_run=False
    #         )
          
            

    for _api, _op_list in OPS_MAP.items():
        if not _api.is_ind:
            continue
        if _api.name not in ("Deutschebahn"):
            continue
        for _op in _op_list:
            run_schemathesis_cmd(
                api_name=_api.name,
                operation_id=_op.id,
                rate_per_minute=get_rate_limit(_api),
                host_url=get_ind_host_url(_api.name),
                max_examples=1000,
                headers=get_token(_api),
                dry_run=False
            )
