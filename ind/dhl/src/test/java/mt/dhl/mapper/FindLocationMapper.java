package mt.dhl.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

public class FindLocationMapper implements CsvRowMapper {
    private final static Properties P = CsvRowMapper.loadProps("dhl.properties");

    @Override
    public LogRecord map(String path, String httpMethod, Map<String, String> row) {
        Map<String, String> n = new HashMap<>();

        // parameters: countryCode, addressLocality, postalCode, streetAddress, providerType, locationType, serviceType, radius, limit, hideClosedLocations, currentDate
        putIfPresent(row, n, "countryCode");
        putIfPresent(row, n, "addressLocality");
        putIfPresent(row, n, "postalCode");
        putIfPresent(row, n, "streetAddress");
        putIfPresent(row, n, "providerType");
        putIfPresent(row, n, "locationType");
        putIfPresent(row, n, "serviceType");
        putIfPresent(row, n, "radius");
        putIfPresent(row, n, "limit");
        putIfPresent(row, n, "hideClosedLocations");
        putIfPresent(row, n, "currentDate");

        Map<String, String> queryParams = new HashMap<>(n);

        LogRecord.Builder b = LogRecord.builder()
                .withPath(path)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams);

        if (isAuthEnabled(row)) {
            addAuth(b);
        }

        return b.build();
    }

    @Override
    public void addAuth(LogRecord.Builder b) {
        b.authApiKeyHeader(P.getProperty("dhl.key.name"), P.getProperty("dhl.key.value"));
    }
}
