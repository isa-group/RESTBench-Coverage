package mt.amadeus;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.amadeus.mapper.HotelOffersMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = AmadeusSutManager.class,
        operationPath = "/v3/shopping/hotel-offers",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = HotelOffersMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/amadeus/get-hotelOffers.yaml",
        removeHeaderFields = {"ama-request-id", "ama-gateway-request-id"},
        removeJsonPaths = {"data[].offers[].id", "data[].offers[].self"},
        restartSutPerInvocation = false,
        sleepAfterEachRequestMs = 1500
)
public class AmadeusHotelEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
