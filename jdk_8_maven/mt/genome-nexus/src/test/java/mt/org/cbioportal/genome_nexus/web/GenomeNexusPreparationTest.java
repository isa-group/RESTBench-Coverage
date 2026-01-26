package mt.org.cbioportal.genome_nexus.web;

import org.junit.jupiter.api.TestTemplate;

import es.us.isa.httpmutator.experiment.endpoint.test.Preparation;
import mt.org.cbioportal.genome_nexus.web.mapper.PostAnnotationMapper;

@Preparation(
    manager = GenomeNexusSutManger.class,
    operationPath = "/annotation",
    httpMethod = "POST",
    model = "/home/ubuntu/exp/services/httpmutator-benchmark/pictModels/genome-nexus/postAnnotation.model",
    delimiter = "*",
    workplace = "target/httpmutator-output",
    removeJsonPaths = {},
    mapper = PostAnnotationMapper.class,
    oas = "/home/ubuntu/exp/services/httpmutator-benchmark/specifications/EMB/genome-nexus.json",
    restartSutPerInvocation = false
)
public class GenomeNexusPreparationTest {
    /**
     * Entry point for the HTTP-mutator extension.
     */
    @TestTemplate
    void test() {
        
    }
}
