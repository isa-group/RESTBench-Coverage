package mt.ohsome;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.ohsome.mapper.GetElementAgg;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = OhsomeSutManager.class,
        operationPath = "/elements/{aggregation}",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = GetElementAgg.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/ohsome/get-elements.yaml",
        restartSutPerInvocation = false
)
public class OhsomeEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
