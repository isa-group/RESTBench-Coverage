package mt.ohsome.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

public class GetElementAgg implements CsvRowMapper {
    @Override
    public LogRecord map(String path, String httpMethod, Map<String, String> row) {
        Map<String, String> n = new HashMap<>();

        //parameters: aggregation, bboxes, bcircles, bpolys, time, filter, showMetadata, timeout
        putIfPresent(row, n, "aggregation");
        putIfPresent(row, n, "bboxes");
        putIfPresent(row, n, "bcircles");
        putIfPresent(row, n, "bpolys");
        putIfPresent(row, n, "time");
        putIfPresent(row, n, "filter");
        putIfPresent(row, n, "showMetadata");
        putIfPresent(row, n, "timeout");

        if (n.containsKey("filter")) {
            n.put("filter", n.get("filter").replace("\"", ""));
        }

        // path parameters: aggregation
        if (!n.containsKey("aggregation")) {
            throw new IllegalArgumentException("Missing required path parameter 'aggregation'");
        }

        // query parameters
        Map<String, String> queryParams = new HashMap<>();
        for (Map.Entry<String, String> e : n.entrySet()) {
            if (!e.getKey().equals("aggregation")) { // path parameter
                queryParams.put(e.getKey(), e.getValue());
            }
        }
        return LogRecord.builder()
                .withPath(path)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams)
                .withPathParameters(Collections.singletonMap("aggregation", n.get("aggregation")))
                .build();
    }
}
