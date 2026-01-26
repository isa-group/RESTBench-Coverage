package mt.com.mongodb.starter;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.com.mongodb.starter.mapper.PostPersonMapper;

@EndpointTest(mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY_REDUCED, // PICT one‐way reduced strength
        level = AssertionLevel.INVARIANT, // Perform Status Code + OAS + Daikon invariant checks + Regression Testing
        workplace = "httpmutator", // Base output directory
        manager = PersonControllerSutManager.class, // Base URI of the service under test
        operationPath = "/api/person",
        httpMethod = "POST",
        removeJsonPaths = {"id", "createdAt", "timestamp"},
        mapper = PostPersonMapper.class, // CsvRowMapper                                                                                             // implementation
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/person/post-person.yaml",
        restartSutPerInvocation = true,
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class PersonControllerEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
        // System.out.println("Executing test with parameters: " +
        // logRecord.toString());
    }
}
