package mt.br.com.codenation.hospital;

import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

import br.com.codenation.hospital.GestaohospitalarApplication;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutUtils;

public class GestaohosiptalSutManager implements SutManager {
    private static final Logger logger = LoggerFactory.getLogger(GestaohosiptalSutManager.class);

    private static final int MONGODB_PORT = 27017;
    private static final String MONGODB_VERSION = "mongo:6.0";
    private static final String MONGODB_DATABASE_PREFIX = "HospitalDB";
   private static final String MONGODB_HOST = "GES-MONGO";
    // private static final String MONGODB_HOST = "localhost";


    @Override
    public SutContext start() {
        final String databaseName = SutUtils.newDbName(MONGODB_DATABASE_PREFIX);
        final String jdbcUrl = String.format("mongodb://%s:%d/%s", MONGODB_HOST, MONGODB_PORT, databaseName);

        ConfigurableApplicationContext ctx = SpringApplication.run(GestaohospitalarApplication.class,
                new String[]{"--server.port=0",
                        "--liquibase.enabled=false",
                        "--spring.data.mongodb.uri=" + jdbcUrl,
                        "--spring.datasource.username=sa",
                        "--spring.datasource.password=\"\"",
                        "--dg-toolkit.derby.port=0",
                        "--spring.cache.type=NONE"
                });
        int port = (Integer) ((Map<?, ?>) ctx.getEnvironment()
                .getPropertySources().get("server.ports").getSource())
                .get("local.server.port");

        String baseUri = String.format("http://localhost:%d", port);
        logger.info("[Gestaohospital] started at {}", baseUri);

        return new SutContext.Builder()
                .baseUri(baseUri)
                .port(port)
                .registerCloseable(ctx)
                .onCleanup(SutUtils.mongoDropDatabase(String.format("mongodb://%s:%d", MONGODB_HOST, MONGODB_PORT), databaseName))
                .build();
    }

    @Override
    public void stop(SutContext sutContext) {
        sutContext.cleanup();
        logger.info("[Gestaohospital] Stopped and cleaned");
    }
}
