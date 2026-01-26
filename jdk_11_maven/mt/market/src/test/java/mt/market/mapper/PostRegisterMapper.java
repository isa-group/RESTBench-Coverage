package mt.market.mapper;

import java.util.HashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PostRegisterMapper implements CsvRowMapper {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "address");
        putIfPresent(row, normalized, "email");
        putIfPresent(row, normalized, "name");
        putIfPresent(row, normalized, "password");
        putIfPresent(row, normalized, "phone");


        ObjectNode objectNode = OBJECT_MAPPER.createObjectNode();
        if (normalized.containsKey("address")) {
            objectNode.put("address", normalized.get("address"));
        }
        if (normalized.containsKey("email")) {
            objectNode.put("email", normalized.get("email"));
        }
        if (normalized.containsKey("name")) {
            objectNode.put("name", normalized.get("name"));
        }
        if (normalized.containsKey("password")) {
            objectNode.put("password", normalized.get("password"));
        }
        if (normalized.containsKey("phone")) {
            objectNode.put("phone", normalized.get("phone"));
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withBodyParameter(objectNode.toString());

        return b.build();
    }
}

