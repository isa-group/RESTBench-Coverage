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

| API | Type | Spec path | Target operation | #Tests @ TCL-4 | #Tests @ TCL-5 | #Tests @ TCL-6 |
| --- | --- | --- | --- | --- | --- | --- |
| ITunes | industrial | `APIs/Industrial/ITunes/getSearch.yaml` | GET /search | 2 | 31 | 678 |
| amadeus | industrial | `APIs/Industrial/amadeus/getV3ShoppingHotel-offers.yaml` | GET /v3/shopping/hotel-offers | 3 | 6 | 30 |
| deutschebahn | industrial | `APIs/Industrial/deutschebahn/getStations.yaml` | GET /stations | 3 | 7 | 27 |
| dhl | industrial | `APIs/Industrial/dhl/getLocation-finderV1Find-by-address.yaml` | GET /location-finder/v1/find-by-address | 2 | 27 | 186 |
| fdic | industrial | `APIs/Industrial/fdic/getInstitutions.yaml` | GET /institutions | 2 | 17 | 201 |
| foursquare | industrial | `APIs/Industrial/foursquare/getPlacesSearch.yaml` | GET /places/search | 4 | 14 | 130 |
| ohsome | industrial | `APIs/Industrial/ohsome/getV1ElementsAggregation.yaml` | GET /v1/elements/{aggregation} | 4 | 10 | 47 |
| stripe | industrial | `APIs/Industrial/stripe/postV1Products.yaml` | POST /v1/products | 4 | 18 | 228 |
| yelp | industrial | `APIs/Industrial/yelp/getBusinessesSearch.yaml` | GET /businesses/search | 3 | 7 | 49 |
| youtube | industrial | `APIs/Industrial/youtube/getYoutubeV3Videos.yaml` | GET /youtube/v3/videos | 4 | 45 | 333 |
| catwatch | open-source | `APIs/Open-source/catwatch/getProjects.json` | GET /projects | 2 | 15 | 155 |
| genome-nexus | open-source | `APIs/Open-source/genome-nexus/postAnnotation.json` | POST /annotation | 2 | 9 | 41 |
| gestaohospital | open-source | `APIs/Open-source/gestaohospital/postV1Hospitais.json` | POST /v1/hospitais | 2 | 5 | 19 |
| languagetool | open-source | `APIs/Open-source/languagetool/postV2Check.json` | POST /v2/check | 4 | 6 | 30 |
| market | open-source | `APIs/Open-source/market/postRegister.json` | POST /register | 2 | 4 | 15 |
| person-controller | open-source | `APIs/Open-source/person-controller/postApiPerson.yaml` | POST /api/person | 2 | 4 | 35 |
| project-tracking-system | open-source | `APIs/Open-source/project-tracking-system/postAppApiAssignments.yaml` | POST /app/api/assignments | 2 | 9 | 44 |
| proxyprint | open-source | `APIs/Open-source/proxyprint/postRequestRegister.json` | POST /request/register | 2 | 7 | 28 |
| scout-api | open-source | `APIs/Open-source/scout-api/postApiV1Activities.json` | POST /api/v1/activities | 4 | 6 | 31 |
| user-management | open-source | `APIs/Open-source/user-management/putUsersId.yaml` | PUT /users/{id} | 3 | 10 | 52 |

