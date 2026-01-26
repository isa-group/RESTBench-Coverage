package mt.org.zalando.catwatch.backend;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import es.us.isa.httpmutator.experiment.pict.CoveringStrength;
import mt.org.zalando.catwatch.backend.mapper.GetProjectMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = CatwatchSutManager.class,
        operationPath = "/projects",
        httpMethod = "GET",
        workplace = "target/httpmutator-output",
        mapper = GetProjectMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/catwatch/get-projects.json",
        removeJsonPaths = {},
        removeJsonNodes = {},
        restartSutPerInvocation = false
)
public class CatwatchEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
