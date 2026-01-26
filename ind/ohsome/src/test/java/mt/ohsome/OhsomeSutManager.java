package mt.ohsome;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class OhsomeSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder().port(0).baseUri("https://api.ohsome.org/v1").build();
    }

    @Override
    public void stop(SutContext sutContext) {

    }
}
