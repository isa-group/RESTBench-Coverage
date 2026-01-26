package mt.amadeus;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.amadeus.mapper.HotelOffersMapper;

@Preparation(
        manager = AmadeusSutManager.class,
        operationPath = "/v3/shopping/hotel-offers",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/amadeus/hotel.model",
        delimiter = "*",
        workplace = "httpmutator",
        mapper = HotelOffersMapper.class,
        removeHeaderFields = {"ama-request-id", "ama-gateway-request-id"},
        removeJsonPaths = {"data[].offers[].id", "data[].offers[].self"},
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/amadeus/get-hotelOffers.yaml",
        restartSutPerInvocation = false,
        sleepAfterEachRequestMs = 1500,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class AmadeusHotelPreparationTest {
    @TestTemplate
    void test() {
    }
}
