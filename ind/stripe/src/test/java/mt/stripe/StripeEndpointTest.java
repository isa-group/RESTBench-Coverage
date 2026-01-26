package mt.stripe;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.stripe.mapper.PostProductMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = StripeSutManager.class,
        operationPath = "/v1/products",
        httpMethod = "POST",
        workplace = "httpmutator",
        mapper = PostProductMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/stripe/post-products-from-agora.yaml",
        removeJsonPaths = {"id", "created", "default_price", "name", "updated", "error.request_log_url"},
        removeHeaderFields = {"original-request", "request-id", "idempotency-key"},
        restartSutPerInvocation = false
)
public class StripeEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
