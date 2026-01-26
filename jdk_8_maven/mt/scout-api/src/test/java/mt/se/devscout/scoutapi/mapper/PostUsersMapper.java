package mt.se.devscout.scoutapi.mapper;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.HashMap;
import java.util.Map;

public class PostUsersMapper implements CsvRowMapper {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();


    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "name");
        putIfPresent(row, normalized, "email_address");
        putIfPresent(row, normalized, "authorization_level");

        ObjectNode objectNode = OBJECT_MAPPER.createObjectNode();
        if (normalized.containsKey("name")) {
            objectNode.put("name", normalized.get("name"));
        }
        if (normalized.containsKey("email_address")) {
            objectNode.put("email_address", normalized.get("email_address"));
        }
        if (normalized.containsKey("authorization_level")) {
            String value = normalized.get("authorization_level");
            try {
                objectNode.put("authorization_level", Integer.parseInt(value));
            } catch (NumberFormatException e) {
                objectNode.put("authorization_level", value);
            }
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withBodyParameter(objectNode.toString());
        if (isAuthEnabled(row)) {
            Map<String, String> headers = new HashMap<>();
            headers.put("Authorization", "ApiKey administrator");
            b.withRequestHeaders(headers);
        }
        return b.build();
    }
}
