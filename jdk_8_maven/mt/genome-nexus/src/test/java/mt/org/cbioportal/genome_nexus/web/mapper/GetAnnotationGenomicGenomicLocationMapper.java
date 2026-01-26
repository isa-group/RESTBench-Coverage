package mt.org.cbioportal.genome_nexus.web;

import java.util.HashMap;
import java.util.Map;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class GetAnnotationGenomicGenomicLocationMapper implements CsvRowMapper {
    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        // Prepare path parameters map and put 'genomicLocation' if present in the CSV row
        Map<String, String> pathParams = new HashMap<>();
        putIfPresent(row, pathParams, "genomicLocation");

        // Prepare query parameters map
        Map<String, String> queryParams = new HashMap<>();
        // Add optional isoformOverrideSource, token, and fields if present
        putIfPresent(row, queryParams, "isoformOverrideSource");
        putIfPresent(row, queryParams, "token");
        putIfPresent(row, queryParams, "fields");

        // Build and return the LogRecord
        return LogRecord.builder()
                .withPath(operationPath)               // set the request path
                .withHttpMethod(httpMethod)            // set the HTTP method (GET, POST, etc.)
                .withPathParameters(pathParams)        // inject any path parameters
                .withQueryParameters(queryParams)      // inject any query parameters
                .build();
    }
}
