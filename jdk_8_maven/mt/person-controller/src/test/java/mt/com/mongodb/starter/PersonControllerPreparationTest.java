package mt.com.mongodb.starter;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.com.mongodb.starter.mapper.PostPersonMapper;

@Preparation(
        manager = PersonControllerSutManager.class,
        operationPath = "/api/person",
        httpMethod = "POST",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/person/post-person.model",
        delimiter = "*",
        workplace = "target/httpmutator-output",
        removeJsonPaths = {"id", "createdAt", "timestamp"},
        mapper = PostPersonMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/specifications/EMB/scout-api.json",
        restartSutPerInvocation = true)
public class PersonControllerPreparationTest {

    @TestTemplate
    void test() {
        // no-op: the extension does the work
    }

}
