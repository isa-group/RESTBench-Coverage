package mt.foursquare;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class FourSquareSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder().port(0).baseUri("https://places-api.foursquare.com").build();
    }

    @Override
    public void stop(SutContext sutContext) {

    }
}
