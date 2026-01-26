package mt.fdic;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class FDICSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder().port(0).baseUri("https://banks.data.fdic.gov/api").build();
    }

    @Override
    public void stop(SutContext sutContext) {

    }
}
