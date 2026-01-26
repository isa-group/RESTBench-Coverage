package mt.deutschebahn;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.deutschebahn.mapper.GetStationMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = DustschebahnSutManager.class,
        operationPath = "/stations",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = GetStationMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/deutschebahn/get-stations.yaml",
        restartSutPerInvocation = false
)
public class DeutscheBahnEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
