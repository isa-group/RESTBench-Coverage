package mt.dhl;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.dhl.mapper.FindLocationMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = DHLSutManager.class,
        operationPath = "/location-finder/v1/find-by-address",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = FindLocationMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/dhl/get-location.yaml",
        restartSutPerInvocation = false,
        sleepAfterEachRequestMs = 1500
)
public class DHLEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
