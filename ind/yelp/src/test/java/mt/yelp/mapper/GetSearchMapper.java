package mt.yelp.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Properties;
import java.util.Set;

public class GetSearchMapper implements CsvRowMapper {

    private static final Properties P = CsvRowMapper.loadProps("yelp.properties");
    
    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "location");
        putIfPresent(row, normalized, "latitude");
        putIfPresent(row, normalized, "longitude");
        putIfPresent(row, normalized, "term");
        putIfPresent(row, normalized, "radius");
        putIfPresent(row, normalized, "categories");
        putIfPresent(row, normalized, "locale");
        putIfPresent(row, normalized, "price");
        putIfPresent(row, normalized, "open_now");
        putIfPresent(row, normalized, "open_at");
        putIfPresent(row, normalized, "attributes");
        putIfPresent(row, normalized, "sort_by");
        putIfPresent(row, normalized, "device_platform");
        putIfPresent(row, normalized, "reservation_date");
        putIfPresent(row, normalized, "reservation_time");
        putIfPresent(row, normalized, "reservation_covers");
        putIfPresent(row, normalized, "matches_party_size_param");
        putIfPresent(row, normalized, "limit");
        putIfPresent(row, normalized, "offset");

        Map<String, String> query = new LinkedHashMap<>();

        if (normalized.containsKey("location")) {
            query.put("location", normalized.get("location"));
        }
        if (normalized.containsKey("latitude")) {
            query.put("latitude", normalized.get("latitude"));
        }
        if (normalized.containsKey("longitude")) {
            query.put("longitude", normalized.get("longitude"));
        }
        if (normalized.containsKey("term")) {
            query.put("term", normalized.get("term"));
        }
        if (normalized.containsKey("radius")) {
            query.put("radius", normalized.get("radius"));
        }
        if (normalized.containsKey("categories")) {
            query.put("categories", normalized.get("categories"));
        }
        if (normalized.containsKey("locale")) {
            query.put("locale", normalized.get("locale"));
        }
        if (normalized.containsKey("price")) {
            query.put("price", normalized.get("price"));
        }
        if (normalized.containsKey("open_now")) {
            query.put("open_now", normalized.get("open_now"));
        }
        if (normalized.containsKey("open_at")) {
            query.put("open_at", normalized.get("open_at"));
        }
        if (normalized.containsKey("attributes")) {
            query.put("attributes", normalized.get("attributes"));
        }
        if (normalized.containsKey("sort_by")) {
            query.put("sort_by", normalized.get("sort_by"));
        }
        if (normalized.containsKey("device_platform")) {
            query.put("device_platform", normalized.get("device_platform"));
        }
        if (normalized.containsKey("reservation_date")) {
            query.put("reservation_date", normalized.get("reservation_date"));
        }
        if (normalized.containsKey("reservation_time")) {
            query.put("reservation_time", normalized.get("reservation_time"));
        }
        if (normalized.containsKey("reservation_covers")) {
            query.put("reservation_covers", normalized.get("reservation_covers"));
        }
        if (normalized.containsKey("matches_party_size_param")) {
            query.put("matches_party_size_param", normalized.get("matches_party_size_param"));
        }
        if (normalized.containsKey("limit")) {
            query.put("limit", normalized.get("limit"));
        }
        if (normalized.containsKey("offset")) {
            query.put("offset", normalized.get("offset"));
        }

        LogRecord.Builder builder = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withQueryParameters(query);

        Map<String, String> headers = new LinkedHashMap<>();

        if (isAuthEnabled(row)) {
            String token = P.getProperty("yelp.key");
            if (token == null || token.isEmpty()) {
                throw new IllegalStateException("Missing yelp.key property");
            }
            headers.put("Authorization", "Bearer " + token);
        }

        if (!headers.isEmpty()) {
            builder.withRequestHeaders(headers);
        }

        return builder.build();
    }
}
