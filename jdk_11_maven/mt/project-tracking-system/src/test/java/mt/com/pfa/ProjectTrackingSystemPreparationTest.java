package mt.com.pfa;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.com.pfa.mapper.PostEmployeesMapper;

@Preparation(
    manager = ProjectTrackingSystemSutManager.class,
    operationPath = "/app/api/employees",
    httpMethod = "POST",
    model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/project-tracking-system/postEmployees.model",
    delimiter = "*",
    workplace = "target/httpmutator-output",
    mapper = PostEmployeesMapper.class,
    oas = "/home/ubuntu/exp/services/httpmutator-benchmark/specifications/REST_GO/project_swagger.yaml",
    removeJsonPaths = {"credential.password"},
    restartSutPerInvocation = true

)
public class ProjectTrackingSystemPreparationTest {
    /**
     * Entry point for the HTTP-mutator extension.
     */
    @TestTemplate
    void test() {
        // This method is intentionally left empty. The actual test logic is handled
        // by the HTTP-mutator extension.
    }
}
