package mt.org.zalando.catwatch.backend.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class GetProjectMapper implements CsvRowMapper {
    private static final DateTimeFormatter TS_FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss");

    private static final List<String> START_DATES;
    private static final List<String> END_DATES;

    static {
        // Fixed base date: 2024-01-01, same as in DatabasePopulator
        LocalDateTime base = LocalDateTime.of(2024, 1, 1, 0, 0);

        START_DATES = Arrays.asList(
                base.plusDays(1).format(TS_FMT),
                base.plusDays(2).format(TS_FMT),
                base.plusDays(3).format(TS_FMT)
        );

        END_DATES = Arrays.asList(
                base.plusDays(7).format(TS_FMT),
                base.plusDays(8).format(TS_FMT),
                base.plusDays(9).format(TS_FMT)
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
        putIfPresent(row, normalized, "language");

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
        if (normalized.containsKey("language")) {
            queryParams.put("language", normalized.get("language"));
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams);

        return b.build();
    }
}
