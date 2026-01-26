package mt.fdic;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.fdic.mapper.GetInstitutionsMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = FDICSutManager.class,
        operationPath = "/institutions",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = GetInstitutionsMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/fdic/get-institutions.yaml",
        restartSutPerInvocation = false,
        sleepAfterEachRequestMs = 1500
)
public class FDICEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
