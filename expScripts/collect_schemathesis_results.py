#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
from pathlib import Path
from urllib.parse import unquote

import requests
import schemathesis as st
import yaml
from deepdiff import DeepHash
from schemathesis import Case
from schemathesis.checks import CHECKS as ST_CHECKS, load_all_checks
from schemathesis.core.failures import FailureGroup
from schemathesis.core.transport import Response as StResponse

from run_evomaster import _resolve_operation_config

BASE_DIR = Path(__file__).parent / "schemathesis-unique-reports"

# Required checks
REQUIRED_CHECKS = [
    "not_a_server_error",
    "status_code_conformance",
    "response_headers_conformance",
    "response_schema_conformance",
    "content_type_conformance",
]

# -------------------------------------------------------------------
# Per-API-operation response normalization config
#   - ignore_fields: fields to ignore in hashing (via DeepHash.exclude_paths)
#   - message_patterns: regex patterns that collapse different concrete
#       error messages into the same abstract "pattern id"
# -------------------------------------------------------------------
OP_RESPONSE_CONFIG = {
    # Example: catwatch / getProject
    #   - Ignore 'timestamp' when hashing 4xx responses
    #   - Normalize certain 'message' values into pattern IDs
    ("Catwatch", "getProjects"): {
        "ignore_fields": ["timestamp"],  # passed to DeepHash as exclude_paths
        "patterns": {
            "message": [
                r"Failed to convert value of type 'java\.lang\.String' to required type 'java\.util\.Date';",
                r"Failed to convert value of type 'java\.lang\.String\[\]' to required type 'java\.util\.Date';",
                r"Failed to convert value of type 'java\.lang.String' to required type 'java\.lang\.Integer';",
                r"Failed to convert value of type 'java\.lang.String\[\]' to required type 'java\.lang\.Integer';"
            ]
        }
    },
    ("ScoutAPI", "postActivities"): {
        "patterns": {
            "message": [
                r"Unable to process JSON"
            ]
        }
    },
    ("LanguageTool", "postCheck"): {
        "patterns": {
            "__root__": [
                r"Set only 'text' or 'data' parameter, not both",
                r"not a language code known to LanguageTool",
                r"Missing 'language' parameter",
                r"Missing 'text' or 'data' parameter",
                r"You specified 'preferredVariants' but you didn't specify 'language=auto'",
                r"'data' key in JSON requires 'text' or 'annotation' key"
            ]
        }
    },
    ("PersonController", "postPerson"): {
        "ignore_fields": ["id"],
    },
    ("UserManagement", "putUsersId"): {
        "ignore_fields": ["timestamp"],
        "patterns": {
            "message": [
                r"The user with Id = .* doesn't exists",
                r"username cannot be null",
                r"Password cannot be null or empty",
                r"Password must to be at least 8 chars, 1 number, 1 upper case, 1 lower case letter, 1 special char, no spaces"
            ]
        }

    },
    ("ProjectTrackingSystem", "postAssignments"): {
        "ignore_fields": [],
        "patterns": {
            "msg": [
                r"Cannot deserialize value of type `java\.time\.LocalDate` from String",
                r"Cannot deserialize value of type `java\.time\.LocalDateTime` from String",
            ]
        }
    },
    ("ProxyPrint", "postRequestRegister"): {
        "ignore_fields": ["timestamp"],
        "patterns": {
            "message": [
                r"no double/Double-argument constructor/factory method to deserialize from Number value",
                r"no String-argument constructor/factory method to deserialize from String value",
                r"no int/Int-argument constructor/factory method to deserialize from Number value",
                r"no long/Long-argument constructor/factory method to deserialize from Number value",
                r"no BigInteger-argument constructor/factory method to deserialize from Number value",
                r"no boolean/Boolean-argument constructor/factory method to deserialize from boolean value",
                r"Cannot deserialize value of type `java\.lang\.String` from Array value",
                r"Cannot deserialize value of type `java\.lang\.String` from Object value",
                r"Cannot deserialize value of type `java\.lang\.Double` from String",
                r"Cannot deserialize value of type `java\.lang\.Double` from Object value",
                r"Cannot deserialize value of type `java\.lang\.Double` from Array value",
                r"Cannot deserialize value of type `java\.lang\.Double` from Boolean value",
                r"Cannot deserialize value of type `long` from Object value",
                r"Cannot deserialize value of type `long` from String",
                r"Cannot deserialize value of type `long` from Array value",
                r"Cannot deserialize value of type `long` from Boolean value",
                r"Cannot deserialize value of type `java\.util\.GregorianCalendar` from Boolean value",
                r"Cannot deserialize value of type `java\.util\.GregorianCalendar` from String",
                r"Cannot deserialize value of type `java\.util\.GregorianCalendar` from Array value",
                r"Cannot deserialize value of type `java\.util\.GregorianCalendar` from Object value",
                r"Cannot deserialize value of type `java\.util\.GregorianCalendar` from Floating-point value",
                r"Cannot deserialize value of type `io\.github\.proxyprint\.kitchen\.models\.printshops\.RegisterRequest` from Array value",
                r"Could not read document: N/A",
                r"Cannot coerce empty String",
                r"out of range of long",
                r"Required request body is missing"
            ]
        }
    },
    ("Gestaohospital", "postHospital"): {
        "ignore_fields": ["timestamp"],
        "patterns": {
            "message": [
                r"no boolean/Boolean-argument constructor/factory method to deserialize from boolean value",
                r"no int/Int-argument constructor/factory method to deserialize from Number value",
                r"no long/Long-argument constructor/factory method to deserialize from Number value",
                r"no BigInteger-argument constructor/factory method to deserialize from Number value",
                r"no String-argument constructor/factory method to deserialize from String value",
                r"Cannot deserialize value of type `java\.lang\.String` from Array value",
                r"Cannot deserialize value of type `java\.lang\.String` from Object value",
                r"Cannot deserialize value of type `int` from Boolean value",
                r"Cannot deserialize value of type `int` from Object value",
                r"Cannot deserialize value of type `int` from String",
                r"Cannot deserialize value of type `int` from Array",
                r"Cannot deserialize value of type `br\.com\.codenation\.hospital\.dto\.HospitalDTO` from Array value",
                r"Cannot coerce empty String",
                r"no double/Double-argument constructor/factory method to deserialize from Number value",
                r"out of range of int",
                r"Required request body is missing",
                r"\[field_sort\] failed to parse field \[order\]"
            ]
        }
    },
    ("AmadeusHotel", "getHotelOffers"): {
        "patterns": {
            "code": [
                3237,
                477,
                1257,
                11,
                425,
                704,
                703
            ]
        }
    },
    ("Deutschebahn", "getStations"): {
        "patterns": {
            "errMsg": [
                r"Illegal parameter",
                r"Illegal Parameter",
                r"Illegal parameter:",
                r"limit must not be empty",
                r"Multiple values are not allowed for limit",
                r"Multiple values are not allowed for offset",
                r"Not Found",
                r"logicaloperator must not be empty",
                r"The value of limit must be a number",
                r"The value of offset must be a number",
            ],
            "moreInformation": [
                r"Request did not match allowed-feature list"
            ]
        }
    },
    ("iTunes", "getSearch"): {
        "patterns": {
            "errorMessage": [
                r"Invalid value\(s\) for key\(s\): \[country\]",
                r"Invalid value\(s\) for key\(s\): \[resultEntity\]",
                r"Invalid value\(s\) for key\(s\): \[attributeType\]",
                r"Invalid value\(s\) for key\(s\): \[language\]",
                r"Invalid value\(s\) for key\(s\): \[mediaType\]",
            ]
        }
    },
    ("DHL", "getFindByAddress"): {
        "patterns": {
            "detail": [
                r"Provided country is not known",
                r"Invalid value for: query parameter countryCode \(missing\)",
                r"Provided locationType is not known",
                r"Invalid value for: query parameter currentDate",
                r"Provided serviceType is not known",
                r"Provided provider is not known",
                r"Radius should be a number between 0 and 1000000",
                r"Invalid parameter type for hideClosedLocations - must be of type Boolean",
            ]
        }
    },
    ("FDIC", "getInstitutions"): {
        "ignore_fields": ["timestamp"],
        "patterns": {
            "detail": [
                r"is not included in the list",
                r"Offset must be greater than or equal to 0",
                r"Offset is not a number",
                r"Offset must be an integer",
                r"Limit must be less than or equal to 10000",
                r"Limit must be an integer",
                r"Limit is not a number",
                r"Limit must be greater than or equal to 0",
                r"search_phase_execution_exception: \[illegal_argument_exception\] Reason: Result window is too large",
                r"Filename can only contain letters, numbers, and",
                r"illegal_argument_exception: \[illegal_argument_exception\] Reason: Failed to parse int parameter \[from\] with",
                r"search_phase_execution_exception: \[parse_exception\]",
                r"search_phase_execution_exception: \[token_mgr_error\] Reason: token_mgr_error",
                r"failed to parse field \[order\]",
                r"Reason: failed to create query"
            ]
        }
    },
    ("Yelp", "getBusinessesSearch"): {
        "patterns": {
            "description": [
                r"is not of type 'number",
                r"is not of type 'integer",
                r"is too short",
                r"does not match '\^\[a-z\]\{2,3\}\_\[A-Z\]\{2\}\$",
                r"is not a 'yelp-supported\-locale'",
                r"Please specify a location or a latitude and longitude",
                r"Not all of the required parameters were passed in",
                r"The open_at provided is too long ago",
                r"Invalid format, expected format is %H:%M",
                r"Invalid format, expected format is %Y-%m-%d",
                r"Could not execute search, try specifying a more exact location",
                r"is not one of \['best_match', 'rating', 'review_count', 'distance'\]"
            ]
        }
    },
    ("Ohsome", "getElementsAggregation"): {
        "ignore_fields": ["requestUrl"],
        "patterns": {
            "message": [
                r"You need to define one of the boundary parameters \(bboxes, bcircles, bpolys\)",
                r"Unknown parameter 'x-schemathesis-unknown-property' for this resource",
                r"Every parameter has to be unique. You can't give more than one",
                r"The given timeout does not fit to its format. Please give one value in seconds and use a point as the decimal delimiter, if needed.",
                r"The given timeout is too long. It has to be shorter than 600.0 seconds",
                r"Your provided boundary parameter \(bboxes, bcircles, or bpolys\) does not fit its format, or you defined more than one boundary parameter.",
                r"Error in processing the boundary parameter. Please remember to follow the format,",
                r"The bpolys parameter must contain double-parseable values in form of lon/lat coordinate pair"
            ]
        }
    },
    ("Stripe", "postV1Products"): {
        "patterns": {
            "message": [
                r"You passed an empty string for 'id'",
                r"You passed an empty string for 'name'",
                r"You passed an empty string for 'marketing_features'",
                r"You passed an empty string for 'default_price_data'",
                r"Received unknown parameter",
                r"Missing required param",
                r"You passed an empty string for 'package_dimensions'",
                r"You passed an empty string for 'description'",
                r"You did not provide an API key."
            ]
        }
    },
    ("YouTube", "getVideos"): {
        "patterns": {
            "message": [
                r"No filter selected. Expected one of:",
                r"Invalid value at 'max_results'",
                r"Invalid value at 'my_rating'",
                r"Invalid value at 'max_height'",
                r"Invalid value at 'max_width'",
                r"Invalid value at 'chart'",
                r"Incompatible parameters specified in the request",
                r"The requested video chart is not supported or is not available"

            ],
            "reason": [
                r"unknownPart",
                r"invalidRegionCode",
                r"unsupportedLanguageCode",
                r"invalidPageToken",
            ]
        }
    }
}


# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------
def get_required_checks(api_name, op_name):
    if api_name == "LanguageTool" and op_name == "postCheck":
        skip = {"content_type_conformance", "response_schema_conformance"}
        return [c for c in REQUIRED_CHECKS if c not in skip]
    return REQUIRED_CHECKS


def get_body_text_from_vcr_response_body(body):
    """
    Extracts the response body text from a VCR-style response structure.

    VCR entries usually store:
        response["body"]["string"]
    which may be either bytes or str.
    """
    s = body.get("string", "")
    if isinstance(s, bytes):
        return s.decode("utf-8", errors="replace")
    return s


import re
from copy import deepcopy


def normalize_message_for_4xx(api_name, op_name, obj):
    """
    Normalize a 4xx response object (dict/list/str) using per-operation patterns.

    OP_RESPONSE_CONFIG[(api_name, op_name)] is expected to contain:
        {
            "patterns": {
                "<field_name>": [regex1, regex2, ...],
                ...
            }
        }

    Behavior:
    ---------
    • Traverse the object recursively.
    • For dicts:
        - If a field has configured patterns and the field value is a string:
            * Try each pattern in order.
            * As soon as one regex matches:
                  → Replace that field value with the regex (or pattern ID)
                  → Record matched_pattern_id
                  → Immediately stop further traversal (short-circuit).
        - Otherwise, recursively check nested dict/list values.
    • For lists:
        - Recursively traverse elements, stopping early if a match occurs.
    • For strings:
        - Optionally apply root-level patterns under "__root__" if configured.
    • For any other type:
        - Return as-is.

    Early stopping:
    ---------------
    Only ONE match is needed. Once the first match is found anywhere in the object, 
    traversal stops and matched_pattern_id is returned.

    Returns:
        (normalized_obj, matched_pattern_id or None)
    """
    config = OP_RESPONSE_CONFIG.get((api_name, op_name), {})
    pattern_config = config.get("patterns") or {}
    matched_pattern_id = None

    # Work on a deep copy so the original obj is not modified
    def _normalize(value):
        nonlocal matched_pattern_id

        # If a pattern was already matched earlier, short-circuit
        if matched_pattern_id is not None:
            return value

        # --- Case 1: value is a dict ----------------------------------------
        if isinstance(value, dict):
            for key, v in value.items():

                # 1) If this field has patterns and the value is a string:
                patterns = pattern_config.get(key)
                if patterns:
                    if isinstance(v, str):
                        for regex in patterns:
                            if not regex:
                                continue
                            if re.search(regex, v):
                                # Pattern matched → normalize and stop traversal
                                matched_pattern_id = regex  # or use a custom ID
                                value[key] = regex  # normalize to pattern ID
                                return value
                    elif isinstance(v, int):
                        for code in patterns:
                            if v == code:
                                matched_pattern_id = str(code)
                                value[key] = str(code)
                                return value

                # 2) Field has patterns and value is a LIST (e.g., msg: ["..."])
                # if patterns and isinstance(v, list):
                #     # Try to match any string element in the list
                #     for idx, elem in enumerate(v):
                #         if not isinstance(elem, str):
                #             continue
                #         for regex in patterns:
                #             if not regex:
                #                 continue
                #             if re.search(regex, elem):
                #                 matched_pattern_id = regex
                #                 value[key] = v
                #                 return value

                # 3) Otherwise, recursively check nested value
                value[key] = _normalize(v)
                if matched_pattern_id is not None:
                    return value

            return value

        # --- Case 2: value is a list ----------------------------------------
        if isinstance(value, list):
            for i, item in enumerate(value):
                value[i] = _normalize(item)
                if matched_pattern_id is not None:
                    return value
            return value

        # --- Case 3: value is a string (e.g., root-level string) -------------
        if isinstance(value, str):
            # Optional root-level patterns (under "__root__")
            root_patterns = pattern_config.get("__root__", [])
            for regex in root_patterns:
                if not regex:
                    continue
                if re.search(regex, value):
                    matched_pattern_id = regex
                    return regex
            return value

        # --- Case 4: scalar (int, float, bool, None, etc.) -------------------
        return value

    normalized_obj = deepcopy(obj)
    normalized_obj = _normalize(normalized_obj)
    if matched_pattern_id is None:
        print(obj)
    return normalized_obj, matched_pattern_id


def safe_sha256hex(obj) -> str:
    """
    Custom hasher for DeepHash that is tolerant to surrogate characters.

    - If obj is bytes: hash directly.
    - Otherwise: convert to str, then encode with 'surrogatepass'
      so that lone surrogates will not raise UnicodeEncodeError.
    """
    if isinstance(obj, bytes):
        data = obj
    else:
        # str() ensures we can handle non-str primitives as well
        data = str(obj).encode("utf-8", errors="surrogatepass")
    return hashlib.sha256(data).hexdigest()


def compute_response_hash(api_name, op_name, body_obj, status_code):
    """
    Compute a DeepHash-based hash for the response body.

    - For non-4xx:
        hash = DeepHash(body_obj)[body_obj]
    - For 4xx:
        * Optionally ignore some fields via exclude_paths
        * Optionally normalize 'message' into a pattern id
        * Then hash the modified copy

    List order is **not** ignored (as per your current requirement).
    """
    is_4xx = isinstance(status_code, int) and 400 <= status_code < 500

    config = OP_RESPONSE_CONFIG.get((api_name, op_name), {})
    ignore_fields = config.get("ignore_fields", [])
    exclude_paths = ignore_fields or None  # DeepHash allows root keys to be passed directly

    if not is_4xx:
        # No special normalization/path exclusion
        hashes = DeepHash(body_obj, exclude_paths=exclude_paths, hasher=safe_sha256hex)
        return str(hashes[body_obj]), None

    config = OP_RESPONSE_CONFIG.get((api_name, op_name), {})
    ignore_fields = config.get("ignore_fields", [])
    exclude_paths = ignore_fields or None  # DeepHash allows root keys to be passed directly

    # Work on a copy for hashing only
    hash_input = deepcopy(body_obj)

    # Normalize message by patterns (if any)
    hash_input, matched_pattern_id = normalize_message_for_4xx(
        api_name,
        op_name,
        hash_input,
    )

    hashes = DeepHash(
        hash_input,
        exclude_paths=exclude_paths,
        hasher=safe_sha256hex,
    )
    return str(hashes[hash_input]), matched_pattern_id


def sample_by_response_size(collected, max_size=100):
    """
    Perform size-based sampling when we have more than max_size responses.

    collected: list of tuples -> (response_size, http_data)

    Logic:
      - If total <= max_size => return all.
      - Otherwise:
          * Sort by response_size ascending.
          * Uniformly pick max_size indices spanning the full size range.
          * This keeps a wide diversity of response sizes.
    """
    n = len(collected)
    if n <= max_size:
        return [item[1] for item in collected]

    collected.sort(key=lambda x: x[0])

    indices = {
        int(round(i * (n - 1) / (max_size - 1)))
        for i in range(max_size)
    }

    sampled = [collected[i][1] for i in sorted(indices)]
    return sampled


load_all_checks()
ALL_CHECKS_BY_NAME = {fn.__name__: fn for fn in ST_CHECKS.get_all()}


def build_operation_case(api_name: str, op_name: str) -> Case:
    op_conf = _resolve_operation_config(api_name, op_name)
    oas_file = op_conf.resolved_oas()
    http_method = op_conf.http_method.upper()
    operation_path = normalize_operation_path(api_name, op_name, op_conf.operation_path)

    schema = st.openapi.from_path(oas_file)
    operation = schema[operation_path][http_method]

    case = operation.Case(path_parameters={"id": 1, "aggregation": "test"})
    return case


def normalize_operation_path(api_name: str, op_name: str, schema_path: str) -> str:
    """
    Centralize path normalization for known schema/recording mismatches.
    """
    if api_name == "ScoutAPI" and op_name == "postActivities":
        return schema_path.replace("/api", "")

    if schema_path == "/v3/shopping/hotel-offers":
        return "/shopping/hotel-offers"

    return schema_path


def extract_interaction_artifacts(http_interaction, target_method: str):
    """
    Parse one VCR http_interaction once, and produce:
      - body_text: str
      - body_obj:  parsed JSON (dict/list) or raw text
      - status_code: int
      - headers_out: dict[str, str]      (for JSONL)
      - st_headers:  dict[str, list[str]] (for Schemathesis StResponse)
      - st_response: StResponse          (for case.validate_response)
    Reuses the same body/header normalization logic for both outputs.
    """
    # ---- status code ----
    status = http_interaction.get("response", {}).get("status", {}) or {}
    status_code = int(status.get("code"))

    # ---- body text + parsed object ----
    body_struct = http_interaction.get("response", {}).get("body", {}) or {}
    body_text = get_body_text_from_vcr_response_body(body_struct)

    try:
        body_obj = json.loads(body_text)
    except json.JSONDecodeError:
        body_obj = body_text

    # ---- headers (VCR raw) ----
    headers_raw = http_interaction.get("response", {}).get("headers", {}) or {}

    # 1) JSONL wants flat dict[str,str] (your existing logic)
    headers_out = {}
    if isinstance(headers_raw, dict):
        for name, value in headers_raw.items():
            if isinstance(value, list):
                headers_out[name] = ", ".join(str(v) for v in value)
            else:
                headers_out[name] = str(value)
    elif isinstance(headers_raw, list):
        for h in headers_raw:
            if isinstance(h, (list, tuple)) and len(h) == 2:
                headers_out[str(h[0])] = str(h[1])
            elif isinstance(h, dict):
                name = h.get("name")
                value = h.get("value")
                if name is not None:
                    headers_out[str(name)] = str(value)

    # 2) Schemathesis wants dict[str, list[str]] with lowercase keys
    st_headers = {}
    if isinstance(headers_raw, dict):
        for k, v in headers_raw.items():
            key = str(k).lower()
            if isinstance(v, list):
                st_headers[key] = [str(x) for x in v]
            else:
                st_headers[key] = [str(v)]
    else:
        # If headers_raw is list-based, best-effort convert
        if isinstance(headers_raw, list):
            tmp = {}
            for h in headers_raw:
                if isinstance(h, (list, tuple)) and len(h) == 2:
                    tmp.setdefault(str(h[0]).lower(), []).append(str(h[1]))
                elif isinstance(h, dict) and h.get("name") is not None:
                    tmp.setdefault(str(h["name"]).lower(), []).append(str(h.get("value")))
            st_headers = tmp

    # ---- build Schemathesis response ----
    content_bytes = body_text.encode("utf-8", errors="replace")
    req_headers_raw = http_interaction.get("request", {}).get("headers", {}) or {}
    req_headers = {}
    if isinstance(req_headers_raw, dict):
        for k, v in req_headers_raw.items():
            if isinstance(v, list):
                req_headers[str(k)] = ", ".join(str(x) for x in v)
            else:
                req_headers[str(k)] = str(v)
    elif isinstance(req_headers_raw, list):
        for h in req_headers_raw:
            if isinstance(h, (list, tuple)) and len(h) == 2:
                req_headers[str(h[0])] = str(h[1])
            elif isinstance(h, dict) and h.get("name") is not None:
                req_headers[str(h["name"])] = str(h.get("value"))
    dummy_request = requests.Request(
        target_method.upper(),
        "http://localhost:8080",
        headers=req_headers,
    ).prepare()

    st_response = StResponse(
        status_code=status_code,
        headers=st_headers,
        content=content_bytes,
        encoding="utf-8",
        elapsed=0.0,
        http_version="1.1",
        message="",
        request=dummy_request,
        verify=True,
    )

    return body_text, body_obj, status_code, headers_out, st_response


# -------------------------------------------------------------------
# Main processing loop
# -------------------------------------------------------------------
def main():
    for _api in BASE_DIR.iterdir():
        if not _api.is_dir():
            continue

        for _op in _api.iterdir():
            if not _op.is_dir():
                continue

            api_name = _api.name
            op_name = _op.name
            print(f"Processing API={api_name}  OP={op_name}")

            # Will store: (response_size, http_data)
            collected = []

            # Track deduplicated response hashes per operation
            seen_hashes = set()
            seen_patterns = set()

            # Resolve target HTTP method from EvoMaster operation config
            op_config = _resolve_operation_config(api_name, op_name)
            target_method = op_config.http_method.upper()

            # Locate VCR file for this operation
            try:
                vcr_file = next(f for f in _op.iterdir() if f.name.startswith("vcr"))
            except StopIteration:
                print(f"  No VCR file found under: {_op}")
                continue

            with open(vcr_file, "r") as f:
                vcr_data = yaml.safe_load(f)

            case: Case = build_operation_case(api_name, op_name)

            for http_interaction in vcr_data.get("http_interactions", []):
                # 1. Filter by HTTP method
                if http_interaction["request"]["method"].upper() != target_method:
                    continue

                # 2. Required checks must all be SUCCESS
                required_checks = get_required_checks(api_name, op_name)
                used_checks = [(c["name"], c["status"]) for c in http_interaction.get("checks", []) if c["name"] in required_checks]
                if not used_checks or not all(c[1] == "SUCCESS" for c in used_checks):
                    continue
                used_checks = [c[0] for c in used_checks]

                body_text, body_obj, status_code, headers_out, st_response = extract_interaction_artifacts(http_interaction, target_method)

                try:
                    check_funcs = [ALL_CHECKS_BY_NAME[name] for name in used_checks]
                    case.validate_response(st_response, check_funcs)
                except FailureGroup:
                    continue

                # 5. Compute hash (DeepHash, not ignoring list order)
                resp_hash, matched_pattern_id = compute_response_hash(
                    api_name,
                    op_name,
                    body_obj,
                    status_code,
                )

                if resp_hash in seen_hashes:
                    # Already have an equivalent response for this operation
                    continue
                seen_hashes.add(resp_hash)

                if matched_pattern_id is not None and matched_pattern_id in seen_patterns:
                    # Already have this 4xx pattern recorded
                    continue
                if matched_pattern_id is not None:
                    seen_patterns.add(matched_pattern_id)

                record = {
                    "status_code": status_code,
                    "body_obj": body_obj,
                    "headers_out": headers_out,
                    "checks": used_checks,
                }

                # For 4xx, optionally record which pattern was matched (if any)
                is_4xx = isinstance(status_code, int) and 400 <= status_code < 500
                if is_4xx and matched_pattern_id is not None:
                    record["normalized_message_pattern"] = matched_pattern_id

                # Use raw body size (bytes) for size-based sampling
                resp_size = len(body_text.encode("utf-8"))

                collected.append((resp_size, record))

            if not collected:
                print(f"  No qualified requests for {api_name}/{op_name}")
                continue

            # 7. Separate 4xx and non-4xx responses
            max_size = 100

            collected_4xx = []
            collected_non4xx = []
            for size, rec in collected:
                if is_4xx_http_data(rec):
                    collected_4xx.append((size, rec))
                else:
                    collected_non4xx.append((size, rec))

            # Only downsample non-4xx responses (e.g., 2xx/3xx/5xx)
            if collected_non4xx:
                sampled_non4xx = sample_by_response_size(
                    collected_non4xx,
                    max_size=max_size
                )
            else:
                sampled_non4xx = []

            # Keep ALL 4xx responses without any sampling
            sampled_requests = [hd for _, hd in collected_4xx] + sampled_non4xx

            # 8. Write results to JSONL
            output_file = _op / "httpmutator-inputs.jsonl"
            with open(output_file, "w", encoding="utf-8") as f:
                for idx, rec in enumerate(sampled_requests):
                    item = make_httpmutator_item_from_artifacts(
                        idx=idx,
                        status_code=rec["status_code"],
                        body_obj=rec["body_obj"],
                        headers_out=rec["headers_out"],
                        used_checks=rec["checks"],
                    )
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            print(
                f"  Kept {len(sampled_requests)} requests "
                f"(from {len(collected)} unique responses) "
            )


def url_decode_recursive(obj):
    """
    Recursively URL-decode all strings inside a nested JSON-like object.
    For example: '%2F' → '/', '%3A' → ':', etc.
    """
    if isinstance(obj, str):
        return unquote(obj)

    if isinstance(obj, list):
        return [url_decode_recursive(x) for x in obj]

    if isinstance(obj, dict):
        return {k: url_decode_recursive(v) for k, v in obj.items()}

    return obj


def make_httpmutator_item_from_artifacts(idx: int, status_code: int, body_obj, headers_out: dict, used_checks: list[str]):
    item_id = f"{idx:08d}"

    decoded_body = url_decode_recursive(body_obj)

    return {
        "id": item_id,
        "Status Code": status_code,
        "Body": decoded_body,
        "Headers": headers_out,
        "Checks": used_checks,
    }


def is_4xx_http_data(http_data):
    """
    Helper to check if the response status code in http_data is 4xx.
    """
    try:
        code = int(
            http_data["status_code"]
        )
    except (TypeError, ValueError):
        return False
    return 400 <= code < 500


if __name__ == "__main__":
    main()
