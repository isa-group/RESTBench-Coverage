package mt.amadeus;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class AmadeusSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder()
                .port(0)
                .baseUri("https://test.api.amadeus.com")
                .build();
    }

    @Override
    public void stop(SutContext sutContext) {

    }
}
