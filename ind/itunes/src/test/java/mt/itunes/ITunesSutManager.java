package mt.itunes;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class ITunesSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder().port(0).baseUri("https://itunes.apple.com").build();
    }

    @Override
    public void stop(SutContext sutContext) {

    }
}
