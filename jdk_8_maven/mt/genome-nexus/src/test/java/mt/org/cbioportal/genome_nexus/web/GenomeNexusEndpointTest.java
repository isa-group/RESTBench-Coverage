package mt.org.cbioportal.genome_nexus.web;

import es.us.isa.httpmutator.experiment.endpoint.test.EndpointParameterizedTest;
import es.us.isa.httpmutator.experiment.endpoint.test.EndpointTest;
import es.us.isa.httpmutator.experiment.endpoint.test.assertion.AssertionLevel;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.model.TestMode;
import mt.org.cbioportal.genome_nexus.web.mapper.PostAnnotationMapper;

@EndpointTest(
        mode = TestMode.BLACK,
        strength = CoveringStrength.ONE_WAY_REDUCED,
        level = AssertionLevel.INVARIANT,
        manager = GenomeNexusSutManger.class,
        operationPath = "/annotation",
        httpMethod = "POST",
        workplace = "httpmutator",
        mapper = PostAnnotationMapper.class,
        oas = "/home/ubuntu/exp/services/httpmutator-benchmark/processedSpecs/genome-nexus/post-annotation.json",
        removeJsonPaths = {},
        removeJsonNodes = {},
        restartSutPerInvocation = false,
        java17Exec = "/Users/lixin/.jenv/versions/17/bin/java",
        postmanAssertifyJar = "/home/ubuntu/exp/services/httpmutator-benchmark/expScripts/tools/PostmanAssertify.jar",
        newmanJsFile = "/home/ubuntu/exp/services/httpmutator-benchmark/expScripts/tools/fail-only-fast-min.js"
)
public class GenomeNexusEndpointTest {
    @EndpointParameterizedTest
    void test(LogRecord logRecord) {

    }
}
