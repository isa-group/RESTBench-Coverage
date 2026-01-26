package mt.org.cbioportal.genome_nexus.web;

import java.util.HashMap;
import java.util.Map;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PostAnnotationDbsnpMapper implements CsvRowMapper {

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        // There are no path parameters for this endpoint

        // Prepare query parameters map and add optional parameters if present
        Map<String, String> queryParams = new HashMap<>();
        putIfPresent(row, queryParams, "isoformOverrideSource"); // optional isoform override source
        putIfPresent(row, queryParams, "token"); // optional token map
        putIfPresent(row, queryParams, "fields"); // optional list of fields

        // Extract request body JSON (list of dbSNP variant IDs)
        String variantIdsJson = row.get("variantIds");

        // Build and return the LogRecord
        return LogRecord.builder()
                .withPath(operationPath) // set the request path (/annotation/dbsnp/)
                .withHttpMethod(httpMethod) // set the HTTP method (POST)
                .withQueryParameters(queryParams) // inject any query parameters
                .withBodyParameter(variantIdsJson) // inject the JSON array of variant IDs
                .build();
    }
}
