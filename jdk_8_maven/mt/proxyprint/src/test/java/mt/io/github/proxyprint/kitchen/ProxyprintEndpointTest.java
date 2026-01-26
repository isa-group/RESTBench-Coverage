package mt.io.github.proxyprint.kitchen;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.io.github.proxyprint.kitchen.mapper.PostRequestRegisterMapper;

@EndpointTest(mode = TestMode.WHITE, // Live “white‐box” mode
        strength = CoveringStrength.ONE_WAY_REDUCED, // PICT one‐way reduced strength
        level = AssertionLevel.FIVE_XX, // Perform Status Code + OAS + Daikon invariant checks + Regression Testing
        workplace = "target/httpmutator-output", // Base output directory
        manager = ProxyprintSutManager.class, // Base URI of the service under test
        operationPath = "/users",
        httpMethod = "POST",
        removeJsonNodes = {},
        mapper = PostRequestRegisterMapper.class, // CsvRowMapper                                                                                             // implementation
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/proxyprint/post-adminRegister.json",
        restartSutPerInvocation = true
)
public class ProxyprintEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {}
}
