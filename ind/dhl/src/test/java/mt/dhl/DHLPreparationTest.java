package mt.dhl;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.dhl.mapper.FindLocationMapper;

@Preparation(
        manager = DHLSutManager.class,
        operationPath = "/location-finder/v1/find-by-address",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/dhl/get-location.model",
        delimiter = "*",
        workplace = "httpmutator",
        mapper = FindLocationMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/dhl/get-location.yaml",
        restartSutPerInvocation = false,
        sleepAfterEachRequestMs = 1500,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class DHLPreparationTest {
    @TestTemplate
    void test() {
    }
}
