package mt.se.devscout.scoutapi;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.se.devscout.scoutapi.mapper.PostActivitiesMapper;

@EndpointTest(mode = TestMode.BLACK, // Live “white‐box” mode
        strength = CoveringStrength.ONE_WAY_REDUCED, // PICT one‐way reduced strength
        level = AssertionLevel.INVARIANT, // Perform Status Code + OAS + Daikon invariant checks + Regression Testing
        workplace = "httpmutator", // Base output directory
        manager = ScoutAPISutManager.class, // Base URI of the service under test
        operationPath = "/api/v1/activities", 
        httpMethod = "POST", 
        removeJsonNodes = {"date_created"},
        mapper = PostActivitiesMapper.class, // CsvRowMapper                                                                                             // implementation
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/scout-api/post-activities.json",
        restartSutPerInvocation = true,
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class ScoutAPIEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
        // System.out.println("Executing test with parameters: " +
        // logRecord.toString());
    }
}
