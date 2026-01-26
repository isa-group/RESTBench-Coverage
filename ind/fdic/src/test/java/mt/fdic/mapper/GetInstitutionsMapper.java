package mt.fdic.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class GetInstitutionsMapper implements CsvRowMapper {

    private static final Properties P = CsvRowMapper.loadProps("fdic.properties");
    private static final List<String> FILTER_LINES = loadLines("filters.csv");
    private static final List<String> SEARCH_LINES = loadLines("search.csv");

    @Override
    public LogRecord map(String path, String httpMethod, Map<String, String> row) {
        Map<String, String> n = new HashMap<>();

        // parameters: filters, search, fields, sort_by, sort_order, limit, offset
        putIfPresent(row, n, "filters");
        putIfPresent(row, n, "search");
        putIfPresent(row, n, "fields");
        putIfPresent(row, n, "sort_by");
        putIfPresent(row, n, "sort_order");
        putIfPresent(row, n, "limit");
        putIfPresent(row, n, "offset");

        Map<String, String> queryParams = new LinkedHashMap<>();
        if (n.containsKey("filters")) {
            queryParams.put("filters", resolveIndexedValue(FILTER_LINES, n.get("filters"), "filters"));
        }
        if (n.containsKey("search")) {
            queryParams.put("search", resolveIndexedValue(SEARCH_LINES, n.get("search"), "search"));
        }
        if (n.containsKey("fields")) {
            queryParams.put("fields", n.get("fields"));
        }
        if (n.containsKey("sort_by")) {
            queryParams.put("sort_by", n.get("sort_by"));
        }
        if (n.containsKey("sort_order")) {
            queryParams.put("sort_order", n.get("sort_order"));
        }
        if (n.containsKey("limit")) {
            queryParams.put("limit", n.get("limit"));
        }
        if (n.containsKey("offset")) {
            queryParams.put("offset", n.get("offset"));
        }

        LogRecord.Builder b = LogRecord.builder()
                .withPath(path)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams);

        if (isAuthEnabled(row)) {
            addAuth(b);
        }
        LogRecord l = b.build();
        System.out.println(l.toString());
        return l;
    }

    @Override
    public void addAuth(LogRecord.Builder b) {
        b.authApiKeyQuery("api_key", P.getProperty("fdic.key"));
    }

    private static List<String> loadLines(String resourceName) {
        try (InputStream in = GetInstitutionsMapper.class.getResourceAsStream("/" + resourceName)) {
            if (in == null) {
                throw new IllegalStateException("Resource not found: " + resourceName);
            }
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                List<String> values = new ArrayList<>();
                String line;
                while ((line = reader.readLine()) != null) {
                    String trimmed = line.trim();
                    if (!trimmed.isEmpty()) {
                        values.add(trimmed);
                    }
                }
                return values;
            }
        } catch (IOException e) {
            throw new IllegalStateException("Failed to load resource: " + resourceName, e);
        }
    }

    private static String resolveIndexedValue(List<String> values, String rawIndex, String field) {
        int index;
        try {
            index = Integer.parseInt(rawIndex.trim());
        } catch (NumberFormatException ex) {
            throw new IllegalArgumentException("Invalid numeric index for " + field + ": " + rawIndex, ex);
        }
        if (index < 0 || index >= values.size()) {
            throw new IllegalArgumentException(
                    field + " index out of range (0.." + (values.size() - 1) + "): " + rawIndex);
        }
        return values.get(index);
    }
}
