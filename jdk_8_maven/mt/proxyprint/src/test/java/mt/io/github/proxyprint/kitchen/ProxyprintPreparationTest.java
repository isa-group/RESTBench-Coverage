package mt.io.github.proxyprint.kitchen;
import mt.io.github.proxyprint.kitchen.mapper.PostRequestRegisterMapper;
import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;

@Preparation(
        manager = ProxyprintSutManager.class,
        operationPath = "/request/register",
        httpMethod = "POST",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/proxyprint/post-requestRegister.model",
        delimiter = "*",
        workplace = "target/httpmutator-output",
        removeJsonPaths = {},
        removeJsonNodes = {},
        mapper = PostRequestRegisterMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/proxyprint/post-requestRegister.json",
        restartSutPerInvocation = true)
public class ProxyprintPreparationTest {
    @TestTemplate
    public void testPreparation() {
        // This method is intentionally left empty.
        // The preparation is handled by the Preparation annotation.
    }
}
