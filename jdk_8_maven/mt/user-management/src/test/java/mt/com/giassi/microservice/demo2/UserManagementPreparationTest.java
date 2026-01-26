package mt.com.giassi.microservice.demo2;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.com.giassi.microservice.demo2.mapper.PostUsersMapper;
import org.junit.jupiter.api.TestTemplate;

@Preparation(
        manager = UserManagementSutManager.class,
        operationPath = "/users",
        httpMethod = "POST",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/user-management/post-users.model",
        delimiter = "*",
        workplace = "target/httpmutator-output",
        removeJsonPaths = {},
        removeJsonNodes = {},
        mapper = PostUsersMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/user-management/post-users.yaml",
        restartSutPerInvocation = true)
public class UserManagementPreparationTest {
    @TestTemplate
    void test() {
        // no-op: the extension does the work
    }

}
