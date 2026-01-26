package mt.youtube.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Properties;
import java.util.Set;

public class GetVideosCsvMapper implements CsvRowMapper {

    private static final Properties PROPS = CsvRowMapper.loadProps("youtube.properties");

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();
        putIfPresent(row, normalized, "part");
        putIfPresent(row, normalized, "chart");
        putIfPresent(row, normalized, "id");
        putIfPresent(row, normalized, "myRating");
        putIfPresent(row, normalized, "hl");
        putIfPresent(row, normalized, "maxHeight");
        putIfPresent(row, normalized, "maxResults");
        putIfPresent(row, normalized, "maxWidth");
//        putIfPresent(row, normalized, "onBehalfOfContentOwner");
//        putIfPresent(row, normalized, "pageToken");
        putIfPresent(row, normalized, "regionCode");
//        putIfPresent(row, normalized, "videoCategoryId");

        Map<String, String> queryParams = new LinkedHashMap<>();

        if (normalized.containsKey("part")) {
            queryParams.put("part", normalized.get("part"));
        }
        if (normalized.containsKey("chart")) {
            String chart = normalized.get("chart").trim();
            queryParams.put("chart", chart);
        }
        if (normalized.containsKey("id")) {
            queryParams.put("id", normalized.get("id"));
        }
        if (normalized.containsKey("myRating")) {
            String rating = normalized.get("myRating").trim();
            queryParams.put("myRating", rating);
        }
        if (normalized.containsKey("hl")) {
            queryParams.put("hl", normalized.get("hl").trim());
        }
        if (normalized.containsKey("maxHeight")) {
            queryParams.put("maxHeight", normalized.get("maxHeight"));
        }
        if (normalized.containsKey("maxResults")) {
            queryParams.put("maxResults", normalized.get("maxResults"));
        }
        if (normalized.containsKey("maxWidth")) {
            queryParams.put("maxWidth", normalized.get("maxWidth"));
        }
        if (normalized.containsKey("onBehalfOfContentOwner")) {
            queryParams.put("onBehalfOfContentOwner", normalized.get("onBehalfOfContentOwner"));
        }
        if (normalized.containsKey("pageToken")) {
            queryParams.put("pageToken", normalized.get("pageToken"));
        }
        if (normalized.containsKey("regionCode")) {
            queryParams.put("regionCode", normalized.get("regionCode").trim().toUpperCase());
        }
        if (normalized.containsKey("videoCategoryId")) {
            queryParams.put("videoCategoryId", normalized.get("videoCategoryId").trim());
        }

        LogRecord.Builder builder = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams);

        if (isAuthEnabled(row)) {
            String token = PROPS.getProperty("youtube.bearerToken", "").trim();
            if (!token.isEmpty()) {
                Map<String, String> headers = new LinkedHashMap<>();
                headers.put("Authorization", "Bearer " + token);
                builder.withRequestHeaders(headers);
            }
        }

        return builder.build();
    }
}
