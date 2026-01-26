package mt.youtube;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.youtube.mapper.GetVideosCsvMapper;

@Preparation(
        manager = YoutubeSutManager.class,
        operationPath = "/youtube/v3/videos",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/youtube/get-videos.model",
        delimiter = "*",
        workplace = "httpmutator",
        mapper = GetVideosCsvMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/youtube/get-videos.yaml",
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class YoutubePreparationTest {
    @TestTemplate
    void test() {
    }
}
