package mt.yelp;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.yelp.mapper.GetSearchMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = YelpSutManager.class,
        operationPath = "/businesses/search",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = GetSearchMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/yelp/get-search.yaml",
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
        restartSutPerInvocation = false
)
public class YelpEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
