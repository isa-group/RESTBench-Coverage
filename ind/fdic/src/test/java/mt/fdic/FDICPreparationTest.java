package mt.fdic;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.fdic.mapper.GetInstitutionsMapper;

@Preparation(
        manager = FDICSutManager.class,
        operationPath = "/institutions",
        httpMethod = "GET",
        model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/FDIC/get-institutions.model",
        delimiter = "*",
        workplace = "httpmutator",
        mapper = GetInstitutionsMapper.class,
        sleepAfterEachRequestMs = 1500,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/fdic/get-institutions.yaml",
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/PostmanAssertify.jar"
)
public class FDICPreparationTest {
    @TestTemplate
    void test() {
    }
}
