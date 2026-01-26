package mt.com.pfa;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class ProjectTrackingSystemSutManager implements SutManager {
    private static final Logger logger = LoggerFactory.getLogger(ProjectTrackingSystemSutManager.class);

    @Override
    public SutContext start() {

        ConfigurableApplicationContext ctx = SpringApplication.run(
                com.pfa.pack.ProjectTrackingSystemApplication.class,
                // dev profile to use the in-memory H2 database
                "--spring.profiles.active=dev",
                "--server.port=0", // use a random port
                // enable Flyway to run migrations
                "--spring.flyway.enabled=true");

        // DataSource ds = ctx.getBean(DataSource.class);
        // logger.info("Initializing H2 in-memory DB from {}", SCRIPT_PATH);
        // try (Connection conn = ds.getConnection();
        //         Reader script = Files.newBufferedReader(SCRIPT_PATH)) {
        //     RunScript.execute(conn, script);
        //     logger.info("H2 initialization complete.");
        // } catch (SQLException | IOException e) {
        //     logger.error("Failed to initialize H2 database", e);
        //     throw new IllegalStateException("Could not initialize H2 from script", e);
        // }

        int port = ctx.getEnvironment().getProperty("local.server.port", Integer.class);
        String baseUri = "http://localhost:" + port;
        logger.info("[ProjectTracking] Spring context started on port {}", port);
        return new SutContext.Builder()
                .baseUri(baseUri)
                .port(port)
                .register(ConfigurableApplicationContext.class, ctx)
                .build();
    }

    @Override
    public void stop(SutContext sutContext) {
        ConfigurableApplicationContext ctx = sutContext.getService(ConfigurableApplicationContext.class);
        if (ctx != null) {
            ctx.close();
            logger.info("[ProjectTracking] Spring context stopped");
        }
    }
}
