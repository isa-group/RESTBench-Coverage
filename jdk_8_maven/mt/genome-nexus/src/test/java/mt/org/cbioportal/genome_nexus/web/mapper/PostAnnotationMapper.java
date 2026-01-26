package mt.org.cbioportal.genome_nexus.web.mapper;

import java.util.HashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

/**
 * Mapper for POST /annotation requests.
 * Parses variants from comma-separated string to JSON array,
 * adds optional query parameters, and constructs a LogRecord.
 */
public class PostAnnotationMapper implements CsvRowMapper {
    private static final JsonNodeFactory NODE_FACTORY = JsonNodeFactory.instance;

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        String variantsRaw = row.get("variants");
        String bodyParam;
    
        if (variantsRaw != null && variantsRaw.trim().equals("-1")) {
            bodyParam = "-1";
        } else {

            ArrayNode variantsArray = parseVariants(variantsRaw);
            bodyParam = variantsArray.toString();
        }

        Map<String, String> queryParams = new HashMap<>();
        putIfPresent(row, queryParams, "isoformOverrideSource");
        putIfPresent(row, queryParams, "token");
        putIfPresent(row, queryParams, "fields");

        // Build and return the LogRecord
        return LogRecord.builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams)
                .withBodyParameter(bodyParam)
                .build();
    }

    /**
     * Parses a comma-separated string of variants into a JSON array node.
     * @param variantsCsv comma-separated variant list (e.g., "v1,v2,v3");
     * @return ArrayNode of variant strings
     * @throws IllegalArgumentException when input is null, blank, or results in no variants
     */
    private ArrayNode parseVariants(String variantsCsv) {
        if (variantsCsv == null || variantsCsv.equals("NULL") || variantsCsv.trim().isEmpty()) {
            throw new IllegalArgumentException("'variants' parameter is required and must not be blank.");
        }

        String[] parts = variantsCsv.split("\\s*,\\s*");
        ArrayNode arrayNode = NODE_FACTORY.arrayNode();
        for (String part : parts) {
            if (part.trim().isEmpty()) {
                continue;
            }
            arrayNode.add(part);
        }

        if (arrayNode.isEmpty()) {
            throw new IllegalArgumentException(
                String.format("Parsed variants list is empty. Input was: '%s'", variantsCsv)
            );
        }
        return arrayNode;
    }
}
