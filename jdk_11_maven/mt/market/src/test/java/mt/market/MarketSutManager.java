package mt.market;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;
import java.util.Map;

public class MarketSutManager implements SutManager {

    private static final Logger log = LoggerFactory.getLogger(MarketSutManager.class);

    private static final String H2_URL = "jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1;";
    private static final String SCHEMA_SQL = "/schema.sql";
    private static final String DATA_SQL = "/data.sql";

    @Override
    public SutContext start() {
        ConfigurableApplicationContext ctx = getConfigurableApplicationContext();

        int port = (Integer) ((Map<?, ?>) ctx.getEnvironment()
                .getPropertySources()
                .get("server.ports")
                .getSource())
                .get("local.server.port");
        String baseUri = "http://localhost:" + port;
        log.info("[Market] started at {}", baseUri);

        return new SutContext.Builder()
                .baseUri(baseUri)
                .port(port)
                .register(ConfigurableApplicationContext.class, ctx)
                .build();
    }

    private static ConfigurableApplicationContext getConfigurableApplicationContext() {
        SpringApplication app = new SpringApplication(market.RestApplication.class);
        ConfigurableApplicationContext ctx = app.run(
                "--server.port=0",
                "--spring.datasource.url=" + H2_URL,
                "--spring.jpa.hibernate.ddl-auto=none",
                "spring.datasource.continue-on-error=false",
                "--spring.datasource.initialization-mode=always",
                "--spring.datasource.schema=classpath:/schema.sql",
                "--spring.datasource.data=classpath:/data.sql"
        );
        return ctx;
    }

    @Override
    public void stop(SutContext sutContext) {
        ConfigurableApplicationContext ctx = sutContext.getService(ConfigurableApplicationContext.class);
        if (ctx != null) {
            ctx.close();
            log.info("[Market] Spring context closed");
        }
    }
}