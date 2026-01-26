import json
from op_configs import OPS_MAP, SCRIPT_DIR

SCH_ROOT_DIR = SCRIPT_DIR / "schemathesis-unique-reports"
EVO_ROOT_DIR = SCRIPT_DIR.parent / "httpmutator-rq3" / "src" / "test" / "resources"

def generate_restats_config_for_sch():
    print("[SCH] Generating restats configs for Schemathesis results...")

    for api, op_list in OPS_MAP.items():
        api_dir = SCH_ROOT_DIR / api.name
        if not api_dir.exists():
            print(f"[SCH][SKIP] API dir not found: {api_dir}")
            continue
        for op in op_list:
            op_dir = api_dir / op.id
            if not op_dir.exists():
                print(f"[SCH][SKIP] Operation dir not found: {op_dir}")
                continue
            restats_config_path = op_dir / "restats-config.json"
            # if restats_config_path.exists():
            #     print(f"Schemathesis: restats config for {api.name}.{op.id} has already existed!")
            #     continue
            action = "OVERWRITE" if restats_config_path.exists() else "CREATE"

            oas_path = op.resolved_oas()
            dumps_dir = op_dir / "dumps"
            report_dir = op_dir / "reporter"
            db_path = op_dir / "database.sqlite"

            dumps_dir.mkdir(exist_ok=True) 
            report_dir.mkdir(exist_ok=True)

            to_write = {
                "modules": "all",
                "specification": str(oas_path),
                "dumpsDir": str(dumps_dir),
                "reportsDir": str(report_dir),
                "dbPath": str(db_path)
            }

            with restats_config_path.open("w") as fp:
                json.dump(to_write, fp)
            
            print(
                f"[SCH][{action}] {api.name}.{op.id} -> {restats_config_path}"
            )

def generate_restats_config_for_evo():
    print("[EVO] Generating restats configs for EvoMaster results...")

    for api, op_list in OPS_MAP.items():
        for op in op_list:
            work_dir = EVO_ROOT_DIR / f"{api.name}-{op.id}"
            if not work_dir.exists():
                print(f"[EVO][SKIP] Work dir not found: {work_dir}")
                continue
            for config in ("withBasicAssertions", "withoutBasicAssertions"):
                config_dir = work_dir / config
                if not config_dir.exists():
                    print(f"[EVO][SKIP] Config dir not found: {config_dir}")
                    continue
                restats_config_path = config_dir / "restats-config.json"
                # if restats_config_path.exists():
                #     print(f"EvoMaster ({config}): restats config for {api.name}.{op.id} has already existed!")
                #     continue
                action = "OVERWRITE" if restats_config_path.exists() else "CREATE"


                oas_path = op.resolved_oas()
                dumps_dir = config_dir / "dumps"
                report_dir = config_dir / "reporter"
                db_path = config_dir / "database.sqlite"

                dumps_dir.mkdir(exist_ok=True) 
                report_dir.mkdir(exist_ok=True)

                to_write = {
                    "modules": "all",
                    "specification": str(oas_path),
                    "dumpsDir": str(dumps_dir),
                    "reportsDir": str(report_dir),
                    "dbPath": str(db_path)
                }

                with restats_config_path.open("w") as fp:
                    json.dump(to_write, fp)
                
                print(
                    f"[EVO][{action}] {api.name}.{op.id} ({config}) -> {restats_config_path}"
                )


if __name__ == "__main__":
    generate_restats_config_for_sch()
    generate_restats_config_for_evo()