package mt.amadeus.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;
import mt.amadeus.AmadeusTokenProvider;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

public class CitySearchMapper implements CsvRowMapper {
    private final static AmadeusTokenProvider TOKEN_PROVIDER;

    static {
        Properties p = CsvRowMapper.loadProps("amadeus.properties");
        TOKEN_PROVIDER = new AmadeusTokenProvider(p);
    }

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> n = new HashMap<>();
        putIfPresent(row, n, "countryCode");
        putIfPresent(row, n, "keyword");
        putIfPresent(row, n, "max");
        putIfPresent(row, n, "include");

        Map<String, String> queryParams = new HashMap<>();
        if (n.containsKey("countryCode")) {
            queryParams.put("countryCode", n.get("countryCode"));
        }
        if (n.containsKey("keyword")) {
            queryParams.put("keyword", n.get("keyword"));
        }
        if (n.containsKey("max")) {
            queryParams.put("max", n.get("max"));
        }
        if (n.containsKey("include")) {
            queryParams.put("include", n.get("include"));
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams);

        if (isAuthEnabled(row)) {
            addAuth(b);
        }
        return b.build();
    }

    @Override
    public void addAuth(LogRecord.Builder b) {
        String token = null;
        try {
            token = TOKEN_PROVIDER.getAccessToken();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        b.authBearer(token);
    }
}
