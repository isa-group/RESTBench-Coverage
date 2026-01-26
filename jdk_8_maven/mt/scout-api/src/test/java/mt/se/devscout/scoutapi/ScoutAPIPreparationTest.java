package mt.se.devscout.scoutapi;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.se.devscout.scoutapi.mapper.PostActivitiesMapper;

@Preparation(
    manager = ScoutAPISutManager.class, 
    operationPath = "/api/v1/activities", 
    httpMethod = "POST", 
    model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/scout-api/postV2Activities.model", 
    delimiter = "*", 
    workplace = "target/httpmutator-output",
    removeJsonPaths = {}, 
    removeJsonNodes = {"date_created"},
    mapper = PostActivitiesMapper.class, 
    oas = "/home/ubuntu/exp/services/httpmutator-benchmark/specifications/EMB/scout-api.json", 
    restartSutPerInvocation = true)
public class ScoutAPIPreparationTest {
    @TestTemplate
    void test() {
        // no-op: the extension does the work
    }

}
