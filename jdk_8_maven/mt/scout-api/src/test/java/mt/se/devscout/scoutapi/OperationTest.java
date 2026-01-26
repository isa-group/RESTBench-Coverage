package mt.se.devscout.scoutapi;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class OperationTest {
    private static SutContext sutContext;
    private static final SutManager sutManager = new ScoutAPISutManager();
    private static final Logger logger = LoggerFactory.getLogger(OperationTest.class);
    
    /**
     * Manually start MongoDB and then bootstrap the Spring Boot application on port
     * 9090.
     */
    @BeforeAll
    public static void startSut() {
        logger.info("Guava Preconditions loaded from: " +
                com.google.common.base.Preconditions.class
                        .getProtectionDomain()
                        .getCodeSource()
                        .getLocation());
        // sutContext = sutManager.start();
        sutContext = sutManager.start();
        // logger.info("SutContext started with base URI: " + sutContext.getBaseUri());
        logger.info("API is started on port: {}", sutContext.getPort());
    }

    /**
     * Stop the Spring context, close MongoClient, and stop the MongoDB container.
     */
    @AfterAll
    public static void stopSut() {
        sutManager.stop(sutContext);
        logger.info("SutContext stopped.");
    }

    /**
     * Send a POST to /annotation and assert a valid JSON array response.
     */
    @Test
    public void testAnnotationEndpoint() throws Exception {
        logger.info("Running testAnnotationEndpoint...");
        Thread.currentThread().join();
    }
}
