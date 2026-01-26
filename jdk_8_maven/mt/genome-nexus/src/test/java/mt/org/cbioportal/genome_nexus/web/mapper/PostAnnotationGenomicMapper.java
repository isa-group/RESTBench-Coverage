package mt.org.cbioportal.genome_nexus.web;

import java.util.HashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PostAnnotationGenomicMapper implements CsvRowMapper {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {

        Map<String, String> normalized = new HashMap<>();
        putIfPresent(row, normalized, "genomicLocations.chromosome");
        putIfPresent(row, normalized, "genomicLocations.start");
        putIfPresent(row, normalized, "genomicLocations.end");
        putIfPresent(row, normalized, "genomicLocations.referenceAllele");
        putIfPresent(row, normalized, "genomicLocations.variantAllele");
        putIfPresent(row, normalized, "isoformOverrideSource");
        putIfPresent(row, normalized, "token");
        putIfPresent(row, normalized, "fields");

        LogRecord.Builder logRecordBuilder = LogRecord.builder()
                .withPath(operationPath) // set the request path (/annotation/genomic)
                .withHttpMethod(httpMethod); // set the HTTP method (POST)

        if (normalized.containsKey("isoformOverrideSource") || normalized.containsKey("token") || normalized.containsKey("fields")) {
            Map<String, String> queryParams = new HashMap<>();
            if (normalized.containsKey("isoformOverrideSource")) {
                queryParams.put("isoformOverrideSource", normalized.get("isoformOverrideSource"));
            }
            if (normalized.containsKey("token")) {
                queryParams.put("token", normalized.get("token"));
            }
            if (normalized.containsKey("fields")) {
                queryParams.put("fields", normalized.get("fields"));
            }
            logRecordBuilder.withQueryParameters(queryParams); // inject any query parameters
        }

        if (normalized.containsKey("genomicLocations.chromosome") ||
            normalized.containsKey("genomicLocations.start") ||
            normalized.containsKey("genomicLocations.end") ||
            normalized.containsKey("genomicLocations.referenceAllele") ||
            normalized.containsKey("genomicLocations.variantAllele")) {
            ObjectNode genomicLocation = OBJECT_MAPPER.createObjectNode();
            if (normalized.containsKey("genomicLocations.chromosome")) {
                genomicLocation.put("chromosome", normalized.get("genomicLocations.chromosome"));   
            }
            if (normalized.containsKey("genomicLocations.start")) {
                genomicLocation.put("start", Integer.parseInt(normalized.get("genomicLocations.start")));   
            }
            if (normalized.containsKey("genomicLocations.end")) {
                genomicLocation.put("end", Integer.parseInt(normalized.get("genomicLocations.end")));
            }
            if (normalized.containsKey("genomicLocations.referenceAllele")) {
                genomicLocation.put("referenceAllele", normalized.get("genomicLocations.referenceAllele"));   
            }
            if (normalized.containsKey("genomicLocations.variantAllele")) {
                genomicLocation.put("variantAllele", normalized.get("genomicLocations.variantAllele"));
            }
            ArrayNode genomicLocationsArray = OBJECT_MAPPER.createArrayNode();
            genomicLocationsArray.add(genomicLocation);
            logRecordBuilder.withBodyParameter(genomicLocationsArray); // inject the JSON array
        }

        return logRecordBuilder.build();
    }

}
