package mt.org.zalando.catwatch.backend;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.zalando.catwatch.backend.CatWatchBackendApplication;
import org.zalando.catwatch.backend.repo.util.DatabasePopulator;

import java.util.Map;

public class CatwatchSutManager implements SutManager {
    private static Logger logger = LoggerFactory.getLogger(CatwatchSutManager.class);

    @Override
    public SutContext start() {
        String dbName = SutUtils.newDbName("testdb");
        String h2Url = "jdbc:h2:mem:" + dbName + ";DB_CLOSE_DELAY=0;MVCC=true;";

        ConfigurableApplicationContext ctx = SpringApplication.run(CatWatchBackendApplication.class, new String[]{
                "--server.port=0",
                "--spring.datasource.url=" + h2Url,
                "--spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
                "--spring.datasource.username=sa",
                "--spring.datasource.password=\"\""
        });

        DatabasePopulator populator = ctx.getBean(DatabasePopulator.class);
        populator.populateTestData();

        int port = (Integer) ((Map<?, ?>) ctx.getEnvironment()
                .getPropertySources().get("server.ports").getSource())
                .get("local.server.port");
        String baseUri = String.format("http://localhost:%d", port);
        logger.info("[Catwatch]: Running on {}", baseUri);
        return new SutContext.Builder()
                .port(port)
                .baseUri(baseUri)
                .registerCloseable(ctx)
                .onCleanup(SutUtils.h2Shutdown(h2Url, "sa", ""))
                .build();
    }

    @Override
    public void stop(SutContext ctx) {
        ctx.cleanup();
        logger.info("[Catwatch]: Stopped");
    }
}
