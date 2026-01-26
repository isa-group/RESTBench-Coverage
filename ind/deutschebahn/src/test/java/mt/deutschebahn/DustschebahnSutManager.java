package mt.deutschebahn;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class DustschebahnSutManager implements SutManager {
    @Override
    public SutContext start() {
        return new SutContext.Builder().port(0).baseUri("https://apis.deutschebahn.com/db-api-marketplace/apis/station-data/v2").build();
    }

    @Override
    public void stop(SutContext sutContext) {

    }
}
