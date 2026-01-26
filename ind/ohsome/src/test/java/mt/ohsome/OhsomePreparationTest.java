package mt.ohsome;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.ohsome.mapper.GetElementAgg;

@Preparation(
        manager = OhsomeSutManager.class,
        operationPath = "/elements/{aggregation}",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/ohsome/get-elements-agg.model",
        delimiter = "*",
        workplace = "httpmutator",
        mapper = GetElementAgg.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/ohsome/get-elements.yaml",
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class OhsomePreparationTest {
    @TestTemplate
    void test() {
    }
}
