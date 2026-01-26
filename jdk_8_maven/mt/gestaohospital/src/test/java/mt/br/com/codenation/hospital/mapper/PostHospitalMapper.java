package mt.br.com.codenation.hospital.mapper;

import java.util.HashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PostHospitalMapper implements CsvRowMapper {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "address");
        putIfPresent(row, normalized, "availableBeds");
        putIfPresent(row, normalized, "beds");
        putIfPresent(row, normalized, "id");
        putIfPresent(row, normalized, "latitude");
        putIfPresent(row, normalized, "longitude");
        putIfPresent(row, normalized, "name");


        ObjectNode objectNode = OBJECT_MAPPER.createObjectNode();

        if (normalized.containsKey("id")) {
            objectNode.put("id", normalized.get("id"));
        }
        if (normalized.containsKey("name")) {
            objectNode.put("name", normalized.get("name"));
        }
        if (normalized.containsKey("address")) {
            objectNode.put("address", normalized.get("address"));
        }
        if (normalized.containsKey("beds")) {
            String value = normalized.get("beds");
            try {
                objectNode.put("beds", Integer.parseInt(value));
            } catch (NumberFormatException e) {
                objectNode.put("beds", value);
            }
        }
        
        if (normalized.containsKey("availableBeds")) {
            String value = normalized.get("availableBeds");
            try {
                objectNode.put("availableBeds", Integer.parseInt(value));
            } catch (NumberFormatException e) {
                objectNode.put("availableBeds", value);
            }
        }
        
        if (normalized.containsKey("longitude")) {
            String value = normalized.get("longitude");
            try {
                objectNode.put("longitude", Double.parseDouble(value));
            } catch (NumberFormatException e) {
                objectNode.put("longitude", value);
            }
        }
        
        if (normalized.containsKey("latitude")) {
            String value = normalized.get("latitude");
            try {
                objectNode.put("latitude", Double.parseDouble(value));
            } catch (NumberFormatException e) {
                objectNode.put("latitude", value);
            }
        }
        
        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withBodyParameter(objectNode.toString());

        return b.build();
    }
}
