import json
import os
import sys
import yaml
import argparse
import csv
import jsonref

def load_spec(path):
    """
    Load an OpenAPI/Swagger spec from a local JSON or YAML file.
    """
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text)

def dereference_spec(spec, spec_path):
    """
    Fully expand all $ref in the OpenAPI spec using jsonref.
    Handles internal and external references safely by setting base_uri.
    """
    # Determine the directory of the spec file for resolving relative references
    base_path = os.path.dirname(os.path.abspath(spec_path))
    base_uri = f"file://{base_path}/"

    try:
        return jsonref.JsonRef.replace_refs(spec, base_uri=base_uri)
    except Exception as e:
        # Could not resolve some $ref (e.g. missing definitions/components). 
        # Log the failure and continue with the unmodified spec.
        print(f"Warning: failed to dereference spec '{spec_path}': {e}")
        return spec


def count_leaf_parameters(
    schema,
    counting_input=True,
    counting_output=False,
    visited=None
):
    """
    Recursively count "leaf" fields in a JSON schema, with:
      - Cycle detection via `visited` to prevent infinite recursion
      - allOf / oneOf / anyOf: treat as a union of subschemas and sum all leaves
      - additionalProperties: include its leaves if it is an object schema
      - readOnly/writeOnly: skip readOnly fields when counting input; skip writeOnly fields when counting output
    Returns an integer representing the total leaf count.
    """
    if not isinstance(schema, dict):
        return 0

    # Initialize visited set on first invocation
    if visited is None:
        visited = set()

    # Use id(schema) to detect cycles
    schema_id = id(schema)
    if schema_id in visited:
        # Already processed this subtree; avoid infinite recursion
        return 0
    visited.add(schema_id)

    # Skip this node if writeOnly and counting output
    if schema.get("writeOnly", False) and counting_output:
        visited.remove(schema_id)
        return 0
    # Skip this node if readOnly and counting input
    if schema.get("readOnly", False) and counting_input:
        visited.remove(schema_id)
        return 0

    # Handle allOf: sum leaves of all subschemas
    if "allOf" in schema and isinstance(schema["allOf"], list):
        total = 0
        for subschema in schema["allOf"]:
            total += count_leaf_parameters(
                subschema,
                counting_input=counting_input,
                counting_output=counting_output,
                visited=visited
            )
        visited.remove(schema_id)
        return total

    # Handle oneOf: treat as union, sum leaves of all subschemas
    if "oneOf" in schema and isinstance(schema["oneOf"], list):
        total = 0
        for subschema in schema["oneOf"]:
            total += count_leaf_parameters(
                subschema,
                counting_input=counting_input,
                counting_output=counting_output,
                visited=visited
            )
        visited.remove(schema_id)
        return total

    # Handle anyOf: treat as union, sum leaves of all subschemas
    if "anyOf" in schema and isinstance(schema["anyOf"], list):
        total = 0
        for subschema in schema["anyOf"]:
            total += count_leaf_parameters(
                subschema,
                counting_input=counting_input,
                counting_output=counting_output,
                visited=visited
            )
        visited.remove(schema_id)
        return total

    # Determine type: if missing, infer from properties or items; otherwise count as a leaf
    schema_type = schema.get("type")
    if not schema_type:
        if "properties" in schema or "additionalProperties" in schema:
            schema_type = "object"
        elif "items" in schema:
            schema_type = "array"
        else:
            # A genuine leaf node (no type and no child structure)
            visited.remove(schema_id)
            return 1

    total = 0

    # If object, count properties and additionalProperties
    if schema_type == "object":
        props = schema.get("properties", {}) or {}
        for prop_name, prop_schema in props.items():
            # Skip readOnly fields when counting input
            if counting_input and prop_schema.get("readOnly", False):
                continue
            # Skip writeOnly fields when counting output
            if counting_output and prop_schema.get("writeOnly", False):
                continue
            total += count_leaf_parameters(
                prop_schema,
                counting_input=counting_input,
                counting_output=counting_output,
                visited=visited
            )

        # Handle additionalProperties if it is a schema
        addl = schema.get("additionalProperties")
        if isinstance(addl, dict):
            total += count_leaf_parameters(
                addl,
                counting_input=counting_input,
                counting_output=counting_output,
                visited=visited
            )

        # If no properties or additionalProperties contributed, count as one leaf
        visited.remove(schema_id)
        return total if total > 0 else 1

    # If array, count items
    elif schema_type == "array":
        items_schema = schema.get("items", {})
        total = 0
        # If items is a non-empty schema dict, recurse; otherwise treat as one leaf
        if isinstance(items_schema, dict) and items_schema:
            total = count_leaf_parameters(
                items_schema,
                counting_input=counting_input,
                counting_output=counting_output,
                visited=visited
            )
        else:
            total = 1
        visited.remove(schema_id)
        return total

    # For primitive types (string, integer, boolean, etc.), count as one leaf
    else:
        visited.remove(schema_id)
        return 1


def analyze_spec(spec, spec_path):
    """
    Analyze an OpenAPI (v2 or v3) spec object.
    Returns a list of dicts, each containing:
      - api_name
      - path
      - method
      - num_input_parameters          (leaf count of input parameters)
      - response_schemas              (mapping from status_code to True/False if a schema exists)
      - output_parameters_by_status   (mapping from status_code to leaf count of output fields)
    """
    # 1. Dereference all $ref to inline schemas
    spec_deref = dereference_spec(spec, spec_path)
    api_name = os.path.splitext(os.path.basename(spec_path))[0]
    results = []

    # 2. Iterate over all paths
    for path, path_item in spec_deref.get("paths", {}).items():
        # Path-level parameters shared by all operations under this path
        path_level_params = path_item.get("parameters", []) or []

        # 3. Iterate over each HTTP method in this path
        for method, operation in path_item.items():
            if method.lower() not in [
                "get", "put", "post", "delete", "options", "head", "patch", "trace"
            ]:
                continue

            # Merge operation-level parameters with path-level parameters
            op_params = operation.get("parameters", []) or []
            all_params = path_level_params + op_params

            # 4. Count input parameter leaves (skip readOnly fields)
            num_input_parameters = 0
            for param in all_params:
                # If the parameter has a schema, count its leaves
                if "schema" in param and isinstance(param["schema"], dict) and param["schema"]:
                    num_input_parameters += count_leaf_parameters(
                        param["schema"],
                        counting_input=True,
                        counting_output=False
                    )
                # In OpenAPI 3.1+, parameters can define schema under content
                elif "content" in param and isinstance(param["content"], dict):
                    for media_obj in param["content"].values():
                        if "schema" in media_obj and isinstance(media_obj["schema"], dict) and media_obj["schema"]:
                            num_input_parameters += count_leaf_parameters(
                                media_obj["schema"],
                                counting_input=True,
                                counting_output=False
                            )
                else:
                    # No schema or content; treat as a simple primitive parameter (query/header/path/formData)
                    num_input_parameters += 1

            # 5. Handle requestBody (OpenAPI v3): count leaves for all media types if schema exists
            if "requestBody" in operation and isinstance(operation["requestBody"], dict):
                content = operation["requestBody"].get("content", {}) or {}
                for media_obj in content.values():
                    if "schema" in media_obj and isinstance(media_obj["schema"], dict) and media_obj["schema"]:
                        num_input_parameters += count_leaf_parameters(
                            media_obj["schema"],
                            counting_input=True,
                            counting_output=False
                        )

            # 6. Analyze responses: check for schema existence and count output leaves (skip writeOnly fields)
            responses = operation.get("responses", {}) or {}
            resp_schemas = {}
            output_params_by_status = {}

            for status, resp in responses.items():
                schema_found = False
                schema = None

                # OpenAPI v2 style: resp.schema
                if "schema" in resp and isinstance(resp["schema"], dict) and resp["schema"]:
                    schema_found = True
                    schema = resp["schema"]

                # OpenAPI v3 style: resp.content.<media>.schema
                elif "content" in resp and isinstance(resp["content"], dict):
                    for media_obj in resp["content"].values():
                        if "schema" in media_obj and isinstance(media_obj["schema"], dict) and media_obj["schema"]:
                            schema_found = True
                            schema = media_obj["schema"]
                            break

                if schema_found and isinstance(schema, dict):
                    resp_schemas[status] = True
                    output_params_by_status[status] = count_leaf_parameters(
                        schema,
                        counting_input=False,
                        counting_output=True
                    )
                else:
                    resp_schemas[status] = False
                    output_params_by_status[status] = 0

            # 7. Collect the metadata for this operation
            results.append({
                "api_name": api_name,
                "path": path,
                "method": method.upper(),
                "num_input_parameters": num_input_parameters,
                "response_schemas": resp_schemas,
                "output_parameters_by_status": output_params_by_status,
            })

    return results

def collect_spec_files(p):
    spec_files = []
    if os.path.isdir(p):
        for root, dirs, files in os.walk(p):
            for fname in files:
                if fname.lower().endswith(('.json', '.yaml', '.yml')):
                    print(f"Collecting spec file: {os.path.join(root, fname)}")
                    spec_files.append(os.path.join(root, fname))
    elif os.path.isfile(p):
        print(f"Collecting spec file: {p}")
        spec_files.append(p)
    else:
        print(f"Warning: {p} does not exist, skipping.", file=sys.stderr)
    return spec_files


def is_2xx(code):
    return str(code).startswith('2') or str(code) == 'default'


def is_4xx(code):
    return str(code).startswith('4')


def filter_operations_with_2xx_and_4xx(data):
    filtered = []
    for op in data:
        if op['num_input_parameters'] == 0:
            continue
        has_2xx = any(is_2xx(status) and op['response_schemas'].get(status, False)
                      for status in op['response_schemas'])
        has_4xx = any(is_4xx(status) and op['response_schemas'].get(status, False)
                      for status in op['response_schemas'])
        # if has_2xx and has_4xx:
        if has_2xx:
            filtered.append({
                'api_name': op['api_name'],
                'path': op['path'],
                'method': op['method'],
                'num_input_parameters': op['num_input_parameters'],
                'has_2XX': True
            })
    return sorted(filtered, key=lambda x: -x['num_input_parameters'])


def write_filtered_csv(data, output_path=None):
    """
    Write only the filtered operations to CSV with columns:
    api_name, path, method, num_input_parameters, has_2XX_and_4XX_schema
    """
    fieldnames = ['api_name', 'path', 'method', 'num_input_parameters', 'has_2XX']

    if output_path:
        f = open(output_path, 'w', encoding='utf-8', newline='')
    else:
        f = sys.stdout

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for op in data:
        writer.writerow(op)

    if output_path:
        f.close()
        print(f"Filtered CSV results written to {output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output', default='CloseSourcedAPIs.csv',
        help='Output CSV file (default: CloseSourcedAPIs.csv)'
    )
    args = parser.parse_args()

    all_spec_files = []

    from pathlib import Path
    EMB_DIR = Path(__file__).parent.parent / 'specifications' / 'EMB'
    REST_GO_DIR = Path(__file__).parent.parent / 'specifications' / 'REST_GO'
    RESTest_DIR = Path(__file__).parent.parent / 'specifications' / 'RESTest'

    # for d in [EMB_DIR, REST_GO_DIR, RESTest_DIR]:
    #     all_spec_files.extend(collect_spec_files(d))
    for d in [RESTest_DIR,]:
        all_spec_files.extend(collect_spec_files(d))

    if not all_spec_files:
        print("No spec files found.", file=sys.stderr)
        sys.exit(1)

    all_operations = []
    for spec_file in all_spec_files:
        try:
            spec = load_spec(spec_file)
            ops = analyze_spec(spec, spec_file)
            all_operations.extend(ops)
        except Exception as e:
            print(f"Failed to process {spec_file}: {e}", file=sys.stderr)

    # Only keep those operations that have both 2xx and 4xx response schemas
    filtered_operations = filter_operations_with_2xx_and_4xx(all_operations)

    # Write filtered operations to CSV with reduced columns
    write_filtered_csv(filtered_operations, args.output)