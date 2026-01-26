package mt.org.zalando.catwatch.backend;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.org.zalando.catwatch.backend.mapper.GetProjectMapper;
import org.junit.jupiter.api.TestTemplate;

@Preparation(
        manager = CatwatchSutManager.class,
        operationPath = "/project",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/catwatch/get-project.model",
        delimiter = "*",
        workplace = "target/httpmutator-output",
        removeJsonPaths = {},
        removeJsonNodes = {},
        mapper = GetProjectMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/catwatch/get-projects.json",
        restartSutPerInvocation = false)
public class CatwatchPreparationTest {
    @TestTemplate
    void test() {
    }
}
