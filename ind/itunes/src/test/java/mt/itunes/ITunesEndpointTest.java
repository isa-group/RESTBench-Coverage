package mt.itunes;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.itunes.mapper.GetSearchMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = ITunesSutManager.class,
        operationPath = "/search",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = GetSearchMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/ITunes/get-search.yaml",
        restartSutPerInvocation = false,
        sleepAfterEachRequestMs = 3500
)
public class ITunesEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
