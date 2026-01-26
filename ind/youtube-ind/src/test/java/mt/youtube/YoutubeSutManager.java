package mt.youtube;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class YoutubeSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder()
                .port(0)
                .baseUri("https://youtube.googleapis.com")
                .build();
    }

    @Override
    public void stop(SutContext sutContext) {
        // No-op for public API endpoints
    }
}
