package mt.br.com.codenation.hospital;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.br.com.codenation.hospital.mapper.PostHospitalMapper;
import org.junit.jupiter.api.TestTemplate;

@Preparation(
        manager = GestaohosiptalSutManager.class,
        operationPath = "/v1/hospitals",
        httpMethod = "POST",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/gestaohosiptal/post-hospital.model",
        delimiter = "*",
        workplace = "target/httpmutator-output",
        removeJsonPaths = {},
        removeJsonNodes = {},
        mapper = PostHospitalMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/gestaohospital/post-hospital.json",
        restartSutPerInvocation = true)
public class GestaohosiptalPreparationTest {
    @TestTemplate
    void test() {
        // no-op: the extension does the work
    }
}
