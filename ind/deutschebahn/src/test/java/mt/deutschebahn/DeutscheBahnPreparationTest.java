package mt.deutschebahn;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.deutschebahn.mapper.GetStationMapper;

@Preparation(
        manager = DustschebahnSutManager.class,
        operationPath = "/stations",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/dustschebahn/get-station.model",
        delimiter = "*",
        workplace = "httpmutator",
        mapper = GetStationMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/deutschebahn/get-stations.yaml",
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class DeutscheBahnPreparationTest {
    @TestTemplate
    void test() {
    }
}
