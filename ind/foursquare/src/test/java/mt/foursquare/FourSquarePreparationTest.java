package mt.foursquare;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.foursquare.mapper.GetSearchMapper;

@Preparation(
        manager = FourSquareSutManager.class,
        operationPath = "/places/search",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/foursquare/get-places.model",
        delimiter = "*",
        workplace = "httpmutator",
        removeJsonPaths = {},
        removeHeaderFields = {"x-fsq-request-id", "x-timer", "access-control-allow-origin"},
        mapper = GetSearchMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/foursquare/get-places.yaml",
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class FourSquarePreparationTest {
    @TestTemplate
    void test() {
    }
}
