package mt.com.mongodb.starter.mapper;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.HashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;

import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PostPersonMapper implements CsvRowMapper {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "address.city");
        putIfPresent(row, normalized, "address.country");
        putIfPresent(row, normalized, "address.number");
        putIfPresent(row, normalized, "address.postcode");
        putIfPresent(row, normalized, "address.street");
        putIfPresent(row, normalized, "age");
        putIfPresent(row, normalized, "cars[].brand");
        putIfPresent(row, normalized, "cars[].maxSpeedKmH");
        putIfPresent(row, normalized, "cars[].model");
        putIfPresent(row, normalized, "createdAt");
        putIfPresent(row, normalized, "firstName");
        putIfPresent(row, normalized, "id.timestamp");
        putIfPresent(row, normalized, "insurance");
        putIfPresent(row, normalized, "lastName");

        ObjectNode objectNode = OBJECT_MAPPER.createObjectNode();
        if (normalized.containsKey("age")) {
            try {
                objectNode.put("age", Integer.parseInt(normalized.get("age")));
            } catch (NumberFormatException e) {
                objectNode.put("age", normalized.get("age"));
            }
        }
        if (normalized.containsKey("firstName")) {
            objectNode.put("firstName", normalized.get("firstName"));
        }
        if (normalized.containsKey("lastName")) {
            objectNode.put("lastName", normalized.get("lastName"));
        }
        if (normalized.containsKey("createdAt")) {
         
        // handling id.timestamp
        if (normalized.containsKey("id.timestamp")) {
            ObjectNode idNode = objectNode.putObject("id");
            idNode.put("timestamp", Long.parseLong(normalized.get("id.timestamp")));
        }   objectNode.put("createdAt", normalized.get("createdAt"));
        }
        if (normalized.containsKey("insurance")) {
            objectNode.put("insurance", Boolean.parseBoolean(normalized.get("insurance")));
        }
        // handling id.timestamp
        if (normalized.containsKey("id.timestamp")) {
            ObjectNode idNode = objectNode.putObject("id");
            idNode.put("timestamp", Long.parseLong(normalized.get("id.timestamp")));
        }

        // constructing address object
        if (normalized.containsKey("address.city")
                || normalized.containsKey("address.country")
                || normalized.containsKey("address.number")
                || normalized.containsKey("address.postcode")
                || normalized.containsKey("address.street")) {
            ObjectNode addressNode = objectNode.putObject("address");
            if (normalized.containsKey("address.city")) {
                addressNode.put("city", normalized.get("address.city"));
            }
            if (normalized.containsKey("address.country")) {
                addressNode.put("country", normalized.get("address.country"));
            }
            if (normalized.containsKey("address.number")) {
                addressNode.put("number", Integer.parseInt(normalized.get("address.number")));
            }
            if (normalized.containsKey("address.postcode")) {
                addressNode.put("postcode", normalized.get("address.postcode"));
            }
            if (normalized.containsKey("address.street")) {
                addressNode.put("street", normalized.get("address.street"));
            }
        }
        // constructing cars array
        if (normalized.containsKey("cars[].brand")
                || normalized.containsKey("DoublemparseDoublemH")
                || normalized.containsKey("cars[].model")) {
            ArrayNode carsNode = objectNode.putArray("cars");
            // only one car is supported in this example
            ObjectNode carNode = carsNode.addObject();
            if (normalized.containsKey("cars[].brand")) {
                carNode.put("brand", normalized.get("cars[].brand"));   
            }
            if (normalized.containsKey("cars[].maxSpeedKmH")) {
                carNode.put("maxSpeedKmH", Double.parseDouble(normalized.get("cars[].maxSpeedKmH")));
            }
            if (normalized.containsKey("cars[].model")) {
                carNode.put("model", normalized.get("cars[].model"));   
            }
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withBodyParameter(objectNode.toString());
        
        return b.build();
    }
}
