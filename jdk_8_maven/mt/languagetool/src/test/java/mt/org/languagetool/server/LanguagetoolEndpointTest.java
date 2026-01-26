package mt.org.languagetool.server;

import mt.org.languagetool.server.mapper.GetLanguageCsvRowMapper;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import es.us.isa.httpmutator.experiment.pict.CoveringStrength;

@EndpointTest(mode = TestMode.WHITE, // Live “white‐box” mode
        strength = CoveringStrength.ONE_WAY_REDUCED, // PICT one‐way reduced strength
        level = AssertionLevel.FIVE_XX, // Perform Status Code + OAS + Daikon invariant checks + Regression Testing
        workplace = "target/httpmutator-output", // Base output directory
        manager = LanguageToolSutManger.class, // Base URI of the service under test
        operationPath = "/language", // Operation path to invoke
        httpMethod = "GET", // HTTP method to use
        mapper = GetLanguageCsvRowMapper.class, // CsvRowMapper implementation
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/specifications/EMB/languagetool.json", // Path to OpenAPI
        removeJsonPaths = {}, restartSutPerInvocation = false // Do not restart the SUT per invocation
)
public class LanguagetoolEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
        // System.out.println("Executing test with parameters: " +
        // logRecord.toString());
    }
}
