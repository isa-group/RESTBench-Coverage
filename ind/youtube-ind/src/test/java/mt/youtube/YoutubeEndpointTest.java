package mt.youtube;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.youtube.mapper.GetVideosCsvMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY,
        level = AssertionLevel.FIVE_XX,
        manager = YoutubeSutManager.class,
        operationPath = "/youtube/v3/videos",
        httpMethod = "GET",
        workplace = "httpmutator",
        mapper = GetVideosCsvMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/youtube/get-videos.yaml",
        restartSutPerInvocation = false
)
public class YoutubeEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {
    }
}
