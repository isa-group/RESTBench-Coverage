package mt.com.pfa;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import static es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel.FIVE_XX;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.com.pfa.mapper.PostAssignmentMapper;

@EndpointTest(
    mode = TestMode.WHITE, // Live “white‐box” mode
    strength = CoveringStrength.ONE_WAY_REDUCED, // PICT one‐way reduced strength
    level = FIVE_XX, // Perform Status Code + OAS + Daikon invariant checks + Regression Testing
    workplace = "httpmutator", // Base output directory
    manager = ProjectTrackingSystemSutManager.class, // Base URI of the service under test
    operationPath = "/app/api/assignments", // Operation path to invoke
    httpMethod = "POST", // HTTP method to use
    mapper = PostAssignmentMapper.class, // CsvRowMapper implementation
    oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/project-tracking-system/postAssignments.yaml", // Path to OpenAPI
    removeJsonPaths = {}, restartSutPerInvocation = true 
)
public class ProjectTrackingSystemEndpointTest {
     @EndpointParameterizedTest
    void test(LogRecord logRecord) {
        // System.out.println("Executing test with parameters: " +
        // logRecord.toString());
    }
}
