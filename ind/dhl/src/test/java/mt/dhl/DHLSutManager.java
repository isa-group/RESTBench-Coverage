package mt.dhl;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class DHLSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder().port(0).baseUri("https://api-sandbox.dhl.com").build();
    }

    @Override
    public void stop(SutContext sutContext) {

    }
}
