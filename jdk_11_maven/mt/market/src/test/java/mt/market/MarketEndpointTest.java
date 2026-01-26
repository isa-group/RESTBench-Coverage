package mt.market;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import es.us.isa.httpmutator.experiment.pict.CoveringStrength;
import mt.market.mapper.PostRegisterMapper;

@EndpointTest(mode = TestMode.WHITE, // Live “white‐box” mode
        strength = CoveringStrength.ONE_WAY_REDUCED, // PICT one‐way reduced strength
        level = AssertionLevel.FIVE_XX, // Perform Status Code + OAS + Daikon invariant checks + Regression Testing
        workplace = "target/httpmutator-output", // Base output directory
        manager = MarketSutManager.class, // Base URI of the service under test
        operationPath = "/register",
        httpMethod = "POST",
        removeJsonNodes = {},
        mapper = PostRegisterMapper.class, // CsvRowMapper                                                                                             // implementation
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/market/post-register.json",
        restartSutPerInvocation = true
)
public class MarketEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
        // System.out.println("Executing test with parameters: " +
        // logRecord.toString());
    }
}