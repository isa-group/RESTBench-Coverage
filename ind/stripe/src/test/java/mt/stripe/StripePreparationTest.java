package mt.stripe;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.stripe.mapper.PostProductMapper;

@Preparation(
        manager = StripeSutManager.class,
        operationPath = "/v1/products",
        httpMethod = "POST",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/stripe/post-products.model",
        delimiter = "*",
        workplace = "httpmutator",
        removeJsonPaths = {"id", "created", "default_price", "name", "updated", "error.request_log_url"},
        removeHeaderFields = {"original-request", "request-id", "idempotency-key"},
        mapper = PostProductMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/stripe/post-products-from-agora.yaml",
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class StripePreparationTest {
    @TestTemplate
    void test() {
    }
}
