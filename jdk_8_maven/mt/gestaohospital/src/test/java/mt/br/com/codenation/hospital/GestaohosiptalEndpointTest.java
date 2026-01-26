package mt.br.com.codenation.hospital;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import es.us.isa.httpmutator.experiment.pict.CoveringStrength;
import mt.br.com.codenation.hospital.mapper.PostHospitalMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = GestaohosiptalSutManager.class,
        operationPath = "/v1/hospitais/",
        httpMethod = "POST",
        workplace = "target/httpmutator-output",
        mapper = PostHospitalMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/gestaohospital/post-hospital.json",
        removeJsonPaths = {},
        removeJsonNodes = {},
        restartSutPerInvocation = true
)
public class GestaohosiptalEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
