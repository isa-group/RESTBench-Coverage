package mt.org.languagetool.server;

import org.languagetool.server.HTTPServer;
import org.languagetool.server.HTTPServerConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class LanguageToolSutManger implements SutManager {
    private final static Logger logger = LoggerFactory.getLogger(LanguageToolSutManger.class);

    @Override
    public SutContext start() {
        HTTPServerConfig cfg = new HTTPServerConfig(0);
        HTTPServer server = new HTTPServer(cfg, false, null, null);
        server.run();
        String baseUri = String.format("http://localhost:%d/v2", server.getBoundPort());
        logger.warn("[LanguageToolSutManger] Started LanguageTool server at {}", baseUri);
        return new SutContext.Builder()
                .port(server.getBoundPort())
                .baseUri(baseUri)
                .register(HTTPServer.class, server)
                .build();
    }

    @Override
    public void stop(SutContext sct) {
        logger.info("Stopping...");
        HTTPServer httpsServer = sct.getService(HTTPServer.class);
        if (httpsServer != null) {
            httpsServer.stop();
            logger.info("[LanguageTool] Stopped"); 
        }
    }
}
