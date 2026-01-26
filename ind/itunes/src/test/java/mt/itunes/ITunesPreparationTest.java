package mt.itunes;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.itunes.mapper.GetSearchMapper;

@Preparation(
        manager = ITunesSutManager.class,
        operationPath = "/search",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/ITunes/get-search.model",
        delimiter = "*",
        workplace = "httpmutator",
        mapper = GetSearchMapper.class,
        sleepAfterEachRequestMs = 3500,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/ITunes/get-search.yaml",
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class ITunesPreparationTest {
    @TestTemplate
    void test() {
    }
}
