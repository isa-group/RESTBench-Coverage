package mt.io.github.proxyprint.kitchen;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutUtils;
import io.github.proxyprint.kitchen.WebAppConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;

public class ProxyprintSutManager implements SutManager {
    private static final Logger log = LoggerFactory.getLogger(ProxyprintSutManager.class);

    @Override
    public SutContext start() {
        String dbName = SutUtils.newDbName("testdb");
        String h2Url = "jdbc:h2:mem:" + dbName + ";DB_CLOSE_DELAY=0;MVCC=true;";
        Path docs;
        try {
            docs = SutUtils.newTempDir("proxyprint-docs-");
            log.info("Created temporary documents path at {}", docs.toAbsolutePath());
        } catch (IOException e) {
            throw new RuntimeException("Error in creating temp document", e);
        }

        ConfigurableApplicationContext ctx = SpringApplication.run(WebAppConfig.class, new String[]{
                "--server.port=0",
                "--spring.datasource.url=" + h2Url,
                "--spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
                "--spring.datasource.username=sa",
                "--spring.datasource.password",
                "--spring.jpa.show-sql=false",
                "--spring.jpa.hibernate.ddl-auto=create-drop",
                "--documents.path=" + docs.toAbsolutePath()
        });

        @SuppressWarnings("unchecked")
        Integer port = (Integer) ((Map<?, ?>) ctx.getEnvironment()
                .getPropertySources()
                .get("server.ports")
                .getSource())
                .get("local.server.port");
        String baseUri = "http://localhost:" + port;

        log.info("[Proxyprint] SUT started at {}", baseUri);

        return new SutContext.Builder()
                .baseUri(baseUri)
                .port(port)
                .dbName(dbName)
                .registerCloseable(ctx)
                .onCleanup(SutUtils.h2Shutdown(h2Url, "sa", ""))
                .onCleanup(SutUtils.tempDirCleanup(docs))
                .registerCloseable(ctx)
                .build();
    }

    @Override
    public void stop(SutContext sutContext) {
        sutContext.cleanup();
        log.info("[Proxyprint] Stopped and cleaned");
    }
}
