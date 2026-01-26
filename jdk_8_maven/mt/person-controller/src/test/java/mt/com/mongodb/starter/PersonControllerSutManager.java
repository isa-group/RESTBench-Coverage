package mt.com.mongodb.starter;

import java.lang.management.ManagementFactory;
import java.util.Map;
import java.util.Objects;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

import com.mongodb.starter.ApplicationStarter;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class PersonControllerSutManager implements SutManager {
    private static final Logger log = LoggerFactory.getLogger(PersonControllerSutManager.class);

    private static final String MONGO_IMAGE = "mongo:4.4.3";
    private static final int MONGO_PORT = 27017;
    private static final String MONGO_HOST = "PERSON-MONGO"; // compose service name
    // private static final String MONGO_HOST = "localhost";

    @Override
    public SutContext start() {
        // 1) Build a unique database name: users_mt_<pid>_<nano36>
        final String databaseName = SutUtils.newDbName("users_mt_");

        final String jdbcUrl = String.format("mongodb://%s:%d", MONGO_HOST, MONGO_PORT);

        SpringApplication app = new SpringApplication(ApplicationStarter.class);
        ConfigurableApplicationContext ctx = app.run(
                "--server.port=0",
                "--spring.data.mongodb.uri=" + jdbcUrl,
                "--spring.data.mongodb.database=" + databaseName
        );

        @SuppressWarnings("unchecked")
        Integer port = (Integer) ((Map<?, ?>) Objects.requireNonNull(ctx.getEnvironment()
                        .getPropertySources()
                        .get("server.ports"))
                .getSource())
                .get("local.server.port");

        String baseUri = "http://localhost:" + port;
        log.info("[Person Controller] SUT started at {} (mongoUri={})", baseUri, jdbcUrl);

        // 4) 封装返回
        return new SutContext.Builder()
                .baseUri(baseUri)
                .port(port)
                .registerCloseable(ctx)
                .onCleanup(SutUtils.mongoDropDatabase(jdbcUrl, databaseName))
                .build();
    }

    @Override
    public void stop(SutContext ctx) {
        ctx.cleanup();

        log.info("[Person Controller] Stopped and cleaned");
    }
}
