package mt.market;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.market.mapper.PostRegisterMapper;

@Preparation(
        manager = MarketSutManager.class,
        operationPath = "/register",
        httpMethod = "POST",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/market/post-register.model",
        delimiter = "*",
        workplace = "target/httpmutator-output",
        removeJsonPaths = {},
        removeJsonNodes = {},
        mapper = PostRegisterMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/market/post-register.json",
        restartSutPerInvocation = true)
public class MarketPreparationTest {

    @TestTemplate
    void test() {
        // no-op: the extension does the work
    }
}
