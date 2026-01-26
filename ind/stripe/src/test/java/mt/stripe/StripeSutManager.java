package mt.stripe;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class StripeSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder().port(0).baseUri("https://api.stripe.com/").build();
    }

}
