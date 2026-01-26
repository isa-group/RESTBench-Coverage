package mt.org.cbioportal.genome_nexus.web;

import java.util.Map;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutUtils;
import org.cbioportal.genome_nexus.GenomeNexusAnnotation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class GenomeNexusSutManger implements SutManager {
    private static Logger logger = LoggerFactory.getLogger(GenomeNexusSutManger.class);

    private static final int MONGODB_PORT = 27017;
    private static final String MONGODB_IMAGE = "mongo:3.6.2";
    private static final String MONGODB_DB_PREFIX = "annotator";
    private static final String MONGO_HOST = "GENOME-MONGO";
    // private static final String MONGO_HOST = "localhost";

    @Override
    public SutContext start() {
//        final String databaseName = SutUtils.newDbName(MONGODB_DB_PREFIX);
        final String databaseName = "annotator_test";
        final String jdbcUrl = String.format("mongodb://%s:%d", MONGO_HOST, MONGODB_PORT);

        // 3) Launch the Spring Boot app on fixed port
        SpringApplication app = new SpringApplication(GenomeNexusAnnotation.class);
        // app.setLazyInitialization(false);
        ConfigurableApplicationContext ctx = app.run(new String[] {
                "--server.port=0",
                "--spring.data.mongodb.uri=" + jdbcUrl + "/" + databaseName,
                "--spring.cache.type=NONE"
        });
        Integer serverPort = (Integer) ((Map) ctx.getEnvironment()
                .getPropertySources().get("server.ports").getSource())
                .get("local.server.port");
        String baseUri = String.format("http://localhost:%d", serverPort);
        logger.info("[GenomeNexus]: Running on " + baseUri);
        return new SutContext.Builder()
                .baseUri(baseUri)
                .port(serverPort)
                .registerCloseable(ctx)
//                .onCleanup(SutUtils.mongoDropDatabase(jdbcUrl, databaseName))
                .build();
    }

    @Override
    public void stop(SutContext ctx) {
        ctx.cleanup();
        logger.info("[GenomeNexus] Stopped and cleaned");
    }
}
