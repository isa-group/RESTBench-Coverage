package mt.yelp;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.yelp.mapper.GetSearchMapper;

@Preparation(
        manager = YelpSutManager.class,
        operationPath = "/businesses/search",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/yelp/get-search.model",
        delimiter = "*",
        workplace = "httpmutator",
        removeJsonPaths = {},
        removeHeaderFields = {
                "x-zipkin-id",
                "x-proxied",
                "x-served-by",
                "x-routing-service",
                "x-extlb",
                "x-cache",
                "x-cache-hits",
                "via",
                "x-b3-sampled",
                "alt-svc",
                "ratelimit-remaining",
                "ratelimit-resettime",
                "set-cookie",
                "accept-ranges",
                "date"
        },
        mapper = GetSearchMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/yelp/get-search.yaml",
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class YelpPreparationTest {
    @TestTemplate
    void test() {
    }
}
