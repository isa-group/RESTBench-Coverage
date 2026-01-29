# RESTBench-Coverage

Coverage-stratified REST API test suites for 20 APIs with TCL-4/5/6 suites per operation.

**RESTBench-Coverage** is a dataset that provides REST API test suites with
**explicitly defined and strictly increasing coverage strength**.
Its primary contribution is enabling **systematic and fair comparison of REST API
testing techniques** by controlling for test-suite coverage across APIs and operations.

In black-box REST API testing, where source code is typically unavailable, coverage
is defined in terms of how thoroughly test inputs and observable outputs of an API
are exercised. RESTBench-Coverage adopts this notion of **input–output coverage**
to stratify test suites in a consistent and reproducible manner.

OpenAPI specifications are included for all APIs, and SUT code is included for
open-source APIs to support **construction, interpretation, and reuse** of the
test suites.

---

## Benchmark Summary (APIs and Artifacts)

Each API is represented by a single operation in this benchmark. Test suites are
available in TCL-4, TCL-5, and TCL-6 variants per operation under
`Test-suites/<api>/<operation>/TCL-{4,5,6}/`, and each suite includes:
`coveringArray.csv`, `coveringArray.txt`, `requests_responses.csv`, and `responses.jsonl`.

| Category | API (tests folder) | Operation | OpenAPI spec | SUT code |
| --- | --- | --- | --- | --- |
| Industrial | amadeus | getV3ShoppingHotel-offers | `APIs/Industrial/amadeus/get-hotelOffers.yaml` | — |
| Industrial | deutschebahn | getStations | `APIs/Industrial/deutschebahn/get-stations.yaml` | — |
| Industrial | dhl | getLocation-finderV1Find-by-address | `APIs/Industrial/dhl/get-location.yaml` | — |
| Industrial | fdic | getInstitutions | `APIs/Industrial/fdic/get-institutions.yaml` | — |
| Industrial | foursquare | getPlacesSearch | `APIs/Industrial/foursquare/get-places.yaml` | — |
| Industrial | itunes | getSearch | `APIs/Industrial/ITunes/get-search.yaml` | — |
| Industrial | ohsome | getElementsAggregation | `APIs/Industrial/ohsome/get-elements.yaml` | — |
| Industrial | stripe | postV1Products | `APIs/Industrial/stripe/post-products.yaml` | — |
| Industrial | yelp | getBusinessesSearch | `APIs/Industrial/yelp/get-search.yaml` | — |
| Industrial | youtube-ind | getYoutubeV3Videos | `APIs/Industrial/youtube/get-videos.yaml` | — |
| Open-source | catwatch | getProjects | `APIs/Open-source/catwatch/get-projects.json` | `APIs/Open-source/catwatch/Code` |
| Open-source | genome-nexus | postAnnotation | `APIs/Open-source/genome-nexus/post-annotation.json` | `APIs/Open-source/genome-nexus/Code` |
| Open-source | gestaohospital | postV1Hospitais | `APIs/Open-source/gestaohospital/post-hospital.json` | `APIs/Open-source/gestaohospital/Code` |
| Open-source | languagetool | postCheck | `APIs/Open-source/languagetool/post-check.json` | `APIs/Open-source/languagetool/Code` |
| Open-source | market | postRegister | `APIs/Open-source/market/post-register.json` | `APIs/Open-source/market/Code` |
| Open-source | person-controller | postApiPerson | `APIs/Industrial/person/post-person.yaml` | `APIs/Open-source/person-controller/Code` |
| Open-source | project-tracking-system | postAppApiAssignments | `APIs/Open-source/project-tracking-system/postAssignments.yaml` | `APIs/Open-source/project-tracking-system/Code` |
| Open-source | proxyprint | postRequestRegister | `APIs/Open-source/proxyprint/post-requestRegister.json` | `APIs/Open-source/proxyprint/Code` |
| Open-source | scout-api | postApiV1Activities | `APIs/Open-source/scout-api/post-activities.json` | `APIs/Open-source/scout-api/Code` |
| Open-source | user-management | putUsersId | `APIs/Open-source/user-management/put-userId.yaml` | `APIs/Open-source/user-management/Code` |

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

Inputs are derived from the API specification and its implementation, with
enumerations and booleans using their defined value sets and other parameter
types represented with a small set of representative valid values.

### TCL-4 Test Suite
- The lowest coverage level.
- Every input parameter is exercised at least once.
- Derived from a **1-way combinatorial test suite**, with redundancy reduction and
  minimal augmentation to improve response diversity.

### TCL-5 Test Suite
- An intermediate coverage level.
- All input parameters and all status codes defined are exercised at least once.
- Based on a 1-way combinatorial test suite, augmented with additional test cases.

### TCL-6 Test Suite
- The highest coverage level.
- All input parameters, all status codes, and all response properties defined are covered.
- Generated using a 2-way combinatorial approach, further augmented to cover missing
  status codes and response fields.

Together, these definitions provide a clear and operational notion of test-suite
strength.

---

## Repository Structure (Simplified)

APIs
```
Industrial
  amadeus               -> APIs/Industrial/amadeus/get-hotelOffers.yaml
  deutschebahn          -> APIs/Industrial/deutschebahn/get-stations.yaml
  dhl                   -> APIs/Industrial/dhl/get-location.yaml
  fdic                  -> APIs/Industrial/fdic/get-institutions.yaml
  foursquare            -> APIs/Industrial/foursquare/get-places.yaml
  itunes                -> APIs/Industrial/ITunes/get-search.yaml
  ohsome                -> APIs/Industrial/ohsome/get-elements.yaml
  stripe                -> APIs/Industrial/stripe/post-products.yaml
  yelp                  -> APIs/Industrial/yelp/get-search.yaml
  youtube-ind           -> APIs/Industrial/youtube/get-videos.yaml

Open-source
  catwatch              -> APIs/Open-source/catwatch/get-projects.json
                           APIs/Open-source/catwatch/Code
  genome-nexus          -> APIs/Open-source/genome-nexus/post-annotation.json
                           APIs/Open-source/genome-nexus/Code
  gestaohospital        -> APIs/Open-source/gestaohospital/post-hospital.json
                           APIs/Open-source/gestaohospital/Code
  languagetool          -> APIs/Open-source/languagetool/post-check.json
                           APIs/Open-source/languagetool/Code
  market                -> APIs/Open-source/market/post-register.json
                           APIs/Open-source/market/Code
  person-controller     -> APIs/Industrial/person/post-person.yaml
                           APIs/Open-source/person-controller/Code
  project-tracking-system -> APIs/Open-source/project-tracking-system/postAssignments.yaml
                             APIs/Open-source/project-tracking-system/Code
  proxyprint            -> APIs/Open-source/proxyprint/post-requestRegister.json
                           APIs/Open-source/proxyprint/Code
  scout-api             -> APIs/Open-source/scout-api/post-activities.json
                           APIs/Open-source/scout-api/Code
  user-management       -> APIs/Open-source/user-management/put-userId.yaml
                           APIs/Open-source/user-management/Code
```

Test suites
```
Test-suites/<api>/<operation>/{TCL-4,TCL-5,TCL-6}/
  coveringArray.csv
  coveringArray.txt
  requests_responses.csv
  responses.jsonl
```

## File Formats (Test Suites)

This section explains how test suites are represented on disk, from input
combinations to concrete request–response pairs.

### 1) Covering Arrays (coveringArray.*)

Within each operation-level test suite directory, the following files store the
generated input combinations (covering arrays):

- coveringArray.csv
- coveringArray.txt

### 2) Full Test Cases and Responses

Each operation-level test suite directory also includes:

- requests_responses.csv
  The complete set of test cases as request–response pairs for the suite inputs.
- responses.jsonl
  A response-only view of the test cases, with one response per line.

### Directory Layout

All test suites are organized under the `Test-suites/` directory by API, operation,
and coverage strength:

```
Test-suites/<api>/<operation>/{TCL-4,TCL-5,TCL-6}/
```

Within each coverage-level directory, files follow the formats described above.

---

## Supporting Artifacts

Supporting artifacts are provided to make the test suites interpretable and reusable:

- APIs/Industrial/
  Industrial API OpenAPI specifications used to define operations and parameters.
- APIs/Open-source/
  Open-source API OpenAPI specifications and corresponding `Code/` directories.
- Test-suites/
  Coverage-stratified test suites organized by API, operation, and TCL level.
