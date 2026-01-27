# RESTBench-Coverage

**RESTBench-Coverage** is a dataset that provides REST API test suites with
**explicitly defined and strictly increasing coverage strength**.
Its primary contribution is enabling **systematic and fair comparison of REST API
testing techniques** by controlling for test-suite coverage across APIs and operations.

In black-box REST API testing, where source code is typically unavailable, coverage
is defined in terms of how thoroughly test inputs and observable outputs of an API
are exercised. RESTBench-Coverage adopts this notion of **input–output coverage**
to stratify test suites in a consistent and reproducible manner.

OpenAPI specifications, domain definitions, and SUT code are included to support the
**construction, interpretation, and reuse** of the test suites.

---

## Core Contribution: Coverage-Stratified Test Suites

The central artifact of this repository is a collection of test suites organized by
coverage strength. For each API operation, three test suites are provided—**TCL-4**,
**TCL-5**, and **TCL-6**—with strictly increasing coverage strength.

These labels refer to
**[Test Coverage Levels (TCLs)](https://dl.acm.org/doi/10.1145/3340433.3342822)**,
a family of black-box coverage criteria for REST APIs. TCLs quantify how thoroughly
a test suite exercises an API’s observable input–output space, including exercised
input parameters, triggered status codes, and observed response properties.

The same stratification strategy is applied consistently across APIs and operations,
enabling **fair and reproducible comparisons** of testing techniques under controlled
coverage conditions.

---

## Definitions of TCL-4, TCL-5, and TCL-6 Test Suites

The following definitions describe how the three coverage levels are operationalized
in this dataset.

Input domains are defined based on the API specification and its implementation:
- Enumerated and boolean parameters use their complete value sets.
- Other parameter types are assigned a small set of representative valid values.
- Optional parameters explicitly include a `NULL` option.

### TCL-4 Test Suite
- The lowest coverage level.
- Every input parameter is exercised at least once.
- Both **successful responses (2XX status codes)** and **client error responses
  (4XX status codes)** are covered.
- Derived from a **1-way combinatorial test suite**, with redundancy reduction and
  one additional test case designed to trigger a 4XX response.

### TCL-5 Test Suite
- An intermediate coverage level.
- All input parameters and all status codes defined are
  exercised at least once.
- Based on a 1-way combinatorial test suite, augmented with additional test cases to cover missing 4XX status codes.

### TCL-6 Test Suite
- The highest coverage level.
- All input parameters, all status codes, and all response properties defined are covered.
- Generated using a 2-way combinatorial approach, further augmented to cover missing 4XX status codes and response fields.

Together, these definitions provide a clear and operational notion of test-suite
strength.

---

## Dataset Structure and File Formats

This section explains how test suites are represented on disk, from domain
specification to concrete request–response pairs.

### 1) Input Domains for 2XX Requests (domains/)

Input domains for successful responses (2XX status codes) are defined under
the `domains/` directory using `*.model` files.

Each `*.model` file defines the value space for a single API operation, using a
simple format with one parameter per line:

```
<param>: v1 * v2 * v3
```

Optional parameters can include a NULL value to represent absence.

### 2) Input Combinations for 4XX Requests (4xx/)

Input combinations intended to trigger client error responses (4XX status codes)
are provided under the top-level `4xx/` directory.

These files store input parameter-value combinations used to construct requests
designed to trigger 4XX responses.

### 3) Covering Arrays for 2XX Inputs (coveringArray.*)

Within each operation-level test suite directory, the following files store the
generated 2XX input combinations (covering arrays) derived from the
corresponding domain definitions:

- coveringArray.csv
- coveringArray.txt

### 4) Full Test Cases and Responses

Each operation-level test suite directory also includes:

- requests_responses.csv
  The complete set of test cases as request–response pairs for the suite inputs.
- responses.jsonl
  A response-only view of the test cases, with one response per line.

### Directory Layout

All test suites are organized under the `tests/` directory by API, operation,
and coverage strength:

```
tests/<api>/<operation>/{TCL-4,TCL-5,TCL-6}/
```

Within each coverage-level directory, files follow the formats described above.

---

## Supporting Artifacts

Supporting artifacts are provided to make the test suites interpretable and reusable:

- specs/
  Processed OpenAPI specifications used to define operations and parameters.
- domains/
  Input domain definitions (`*.model`) used as the basis for 2XX test case generation.
- 4xx/
  Input parameter-value combinations used to construct requests that trigger
  client error responses (4XX status codes).
- suts/
  SUT source code provided for context and reproducibility.
