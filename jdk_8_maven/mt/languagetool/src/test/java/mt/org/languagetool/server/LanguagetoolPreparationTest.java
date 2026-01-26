package mt.org.languagetool.server;

import org.junit.jupiter.api.TestTemplate;
import mt.org.languagetool.server.mapper.PostCheckCsvRowMapper;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;

@Preparation(
    manager = LanguageToolSutManger.class,
    operationPath = "/language",
    httpMethod = "GET", 
    model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/Languagetool-postCheck.model", 
    delimiter = "*", 
    workplace = "target/httpmutator-output", 
    removeJsonPaths = {}, 
    mapper = PostCheckCsvRowMapper.class,
    oas = "/home/ubuntu/exp/services/httpmutator-benchmark/specifications/EMB/languagetool.json",
    restartSutPerInvocation = false
)
public class LanguagetoolPreparationTest {
    /** 
     * The @TestTemplate is driven by EndpointTestExtension.
     * One invocation per CSV row; no body needed.
     */
    @TestTemplate
    void test() {
        // no-op: the extension does the work
    }
}
