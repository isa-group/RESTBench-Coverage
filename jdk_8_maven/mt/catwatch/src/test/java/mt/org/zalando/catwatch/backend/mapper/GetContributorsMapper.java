package mt.org.zalando.catwatch.backend.mapper;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class GetContributorsMapper implements CsvRowMapper {
    private static final DateTimeFormatter TS_FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'");  

    private static final List<String> START_DATES;
    private static final List<String> END_DATES;

    static {
        LocalDateTime now = LocalDateTime.now();
        START_DATES = Arrays.asList(
                now.minusDays(10).format(TS_FMT),
                now.minusDays(20).format(TS_FMT),
                now.minusDays(30).format(TS_FMT)
        );
        END_DATES = Arrays.asList(
                now.minusDays(0).format(TS_FMT),
                now.minusDays(4).format(TS_FMT),
                now.minusDays(8).format(TS_FMT)
        );
    }

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "organizations");
        putIfPresent(row, normalized, "limit");
        putIfPresent(row, normalized, "offset");
        putIfPresent(row, normalized, "start_date");
        putIfPresent(row, normalized, "end_date");
        putIfPresent(row, normalized, "sortBy");
        putIfPresent(row, normalized, "q");

        Map<String, String> queryParams = new HashMap<>();

        if (normalized.containsKey("organizations")) {
            queryParams.put("organizations", normalized.get("organizations"));
        }
        if (normalized.containsKey("limit")) {
            queryParams.put("limit", normalized.get("limit"));
        }
        if (normalized.containsKey("offset")) {
            queryParams.put("offset", normalized.get("offset"));
        }
        if (normalized.containsKey("start_date")) {
            int i = Integer.parseInt(normalized.get("start_date"));
            if (i >= 0 && i < START_DATES.size()) {
                queryParams.put("start_date", START_DATES.get(i));
            } else {
                throw new IllegalArgumentException("Invalid start_date index: " + i);
            }
        }
        if (normalized.containsKey("end_date")) {
            int i = Integer.parseInt(normalized.get("end_date"));
            if (i >= 0 && i < END_DATES.size()) {
                queryParams.put("end_date", END_DATES.get(i));
            } else {
                throw new IllegalArgumentException("Invalid end_date index: " + i);
            }
        }
        if (normalized.containsKey("sortBy")) {
            queryParams.put("sortBy", normalized.get("sortBy"));
        }
        if (normalized.containsKey("q")) {
            queryParams.put("q", normalized.get("q"));
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams);

        return b.build();
    }
}
