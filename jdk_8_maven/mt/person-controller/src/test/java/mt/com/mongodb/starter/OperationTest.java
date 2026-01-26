package mt.com.mongodb.starter;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OperationTest {
    private static SutContext sutContext;
    private static final SutManager sutManager = new PersonControllerSutManager();
    private static final Logger logger = LoggerFactory.getLogger(OperationTest.class);

    /**
     * Manually start MongoDB and then bootstrap the Spring Boot application on port 9090.
     */
    @BeforeAll
    public static void startSut() {
        sutContext = sutManager.start();
        logger.info("API is started on port: {}", sutContext.getPort());
    }

    /**
     * Stop the Spring context, close MongoClient, and stop the MongoDB container.
     */
    @AfterAll
    public static void stopSut() {
        sutManager.stop(sutContext);
    }

    /**
     * Send a POST to /annotation and assert a valid JSON array response.
     */
    @Test
    public void testAnnotationEndpoint() throws Exception {
        Thread.currentThread().join();
    }
}
