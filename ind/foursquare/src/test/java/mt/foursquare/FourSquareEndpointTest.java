package mt.foursquare;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.foursquare.mapper.GetSearchMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = FourSquareSutManager.class,
        operationPath = "/places/search",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = GetSearchMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/foursquare/get-places.yaml",
        removeHeaderFields = {"x-fsq-request-id", "x-timer", "access-control-allow-origin"},
        restartSutPerInvocation = false
)
public class FourSquareEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
