`mvn test -Dsurefire.includes="**/ProjectTrackingSystem/**/*_Test.java"`

```java
given()
    .filter(filter)
    .accept("*/*")
    .post(baseUrlOfSut + "/v2/check")
    .statuscode(500);
```

```java
HttpmutatorFilter filter = new HTTPmutatorFilter();
given()
    .filter(filter)
    .accept("*/*")
    .post(baseUrlOfSut + "/v2/check");  

Consumer<ValidatableResponse> assertFunc = vr -> vr.statusCode(500);
filter.assertMutants(assertFunc)

```