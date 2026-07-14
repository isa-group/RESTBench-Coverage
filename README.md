# RESTBench-Coverage

RESTBench-Coverage is a dataset of REST API test suites with explicitly defined, strictly increasing coverage strength based on [REST API testing coverage criteria](https://personal.us.es/amarlop/wp-content/uploads/2019/09/Test_Coverage_Criteria_for_RESTful_Web_APIs.pdf).


## Definitions of TCL-4, TCL-5, and TCL-6 Test Suites

Each test suite in the dataset is assigned to one of three coverage levels (TCL-4, TCL-5, TCL-6), where higher levels strictly subsume the lower ones. The definitions below specify how these levels are instantiated for each target operation.

### Input domains

For test generation, we derive input domains from the API specification (and, when needed, implementation constraints). In particular:

- Enumerated and boolean parameters use their complete value sets.
- Other parameter types are assigned a small set of representative valid values.
- Optional parameters explicitly include a NULL option.

### TCL-4 Test Suite
- The lowest coverage level.
- The main test suite targets successful executions (2XX) and ensures that every input parameter is exercised at least once with a non-null value.
- In addition, extra 4XX-triggering inputs are provided to cover client error responses (4XX).

### TCL-5 Test Suite
- An intermediate coverage level.
- The main test suite targets successful executions (2XX) and ensures that every input parameter value is exercised, and that all defined 2XX status codes are exercised at least once.
- In addition, extra 4XX-triggering inputs are provided to cover missing 4XX status codes defined for the operation.

### TCL-6 Test Suite
- The highest coverage level.
- The main test suite targets successful executions (2XX) and ensures that, for any pair of two input parameters, all combinations of their values (w.r.t. the input domains defined above) are exercised.
- In addition, extra 4XX-triggering inputs are provided to cover missing 4XX status codes and response fields not exercised by the main suite.


## Benchmark Summary

The dataset contains 32 target operations across 20 APIs, with 3,406 recorded tests in 96 test suites.

For Scout API activity creation, `POST /api/v1/activities` and `POST /api/v2/activities` refer to the same operation and are represented by a single benchmark entry.

| API | Type | Target operation | #Tests @ TCL-4 | #Tests @ TCL-5 | #Tests @ TCL-6 |
| --- | --- | --- | --- | --- | --- |
| ITunes | industrial | GET /search | 2 | 31 | 678 |
| amadeus | industrial | GET /v3/shopping/hotel-offers | 3 | 6 | 30 |
| deutschebahn | industrial | GET /stations | 3 | 7 | 27 |
| dhl | industrial | GET /location-finder/v1/find-by-address | 2 | 27 | 186 |
| fdic | industrial | GET /institutions | 2 | 17 | 201 |
| foursquare | industrial | GET /places/search | 4 | 14 | 130 |
| ohsome | industrial | GET /v1/elements/{aggregation} | 4 | 10 | 47 |
| stripe | industrial | POST /v1/products | 4 | 18 | 228 |
| yelp | industrial | GET /businesses/search | 3 | 7 | 49 |
| youtube | industrial | GET /youtube/v3/videos | 4 | 45 | 333 |
| catwatch | open-source | GET /projects | 2 | 15 | 155 |
| catwatch | open-source | GET /contributors | 2 | 27 | 261 |
| genome-nexus | open-source | POST /annotation | 2 | 9 | 41 |
| gestaohospital | open-source | POST /v1/hospitais | 2 | 5 | 19 |
| gestaohospital | open-source | PUT /v1/hospitais/{hospital_id}/pacientes/{patientId} | 3 | 10 | 66 |
| gestaohospital | open-source | POST /v1/hospitais/{hospital_id}/pacientes/checkin | 3 | 6 | 37 |
| gestaohospital | open-source | PUT /v1/hospitais/{hospital_id} | 2 | 5 | 25 |
| languagetool | open-source | POST /v2/check | 4 | 6 | 30 |
| market | open-source | POST /register | 2 | 4 | 15 |
| market | open-source | PUT /customer/cart | 2 | 14 | 36 |
| market | open-source | PUT /customer/contacts | 2 | 5 | 8 |
| person-controller | open-source | POST /api/person | 2 | 4 | 35 |
| person-controller | open-source | PUT /api/person | 2 | 4 | 34 |
| project-tracking-system | open-source | POST /app/api/assignments | 2 | 9 | 44 |
| project-tracking-system | open-source | POST /app/api/employees | 2 | 6 | 28 |
| project-tracking-system | open-source | POST /app/api/departments | 3 | 4 | 10 |
| proxyprint | open-source | POST /request/register | 2 | 7 | 28 |
| proxyprint | open-source | POST /admin/register | 1 | 4 | 24 |
| scout-api | open-source | POST /api/v1/activities | 4 | 6 | 31 |
| scout-api | open-source | PUT /api/v2/activities/{id} | 3 | 8 | 42 |
| user-management | open-source | PUT /users/{id} | 3 | 10 | 52 |
| user-management | open-source | POST /users | 3 | 5 | 37 |
