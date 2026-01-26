package mt.market;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OperationTest {
    private static SutContext sutContext;
    private static final SutManager sutManager = new MarketSutManager();
    private static final Logger logger = LoggerFactory.getLogger(OperationTest.class);

    @BeforeAll
    public static void startSut() {
        sutContext = sutManager.start();
        logger.info("API is started on port: {}", sutContext.getPort());
    }

    @AfterAll
    public static void stopSut() {
        sutManager.stop(sutContext);
    }

    @Test
    public void testAnnotationEndpoint() throws Exception {
        Thread.currentThread().join();
    }
}
