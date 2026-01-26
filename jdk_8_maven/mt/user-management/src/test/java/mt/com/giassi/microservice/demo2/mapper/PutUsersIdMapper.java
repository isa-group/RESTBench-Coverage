package mt.com.giassi.microservice.demo2.mapper;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.HashMap;
import java.util.Map;

public class PutUsersIdMapper implements CsvRowMapper {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();
        putIfPresent(row, normalized, "id");
        putIfPresent(row, normalized, "address");
        putIfPresent(row, normalized, "address2");
        putIfPresent(row, normalized, "birthDate");
        putIfPresent(row, normalized, "city");
        putIfPresent(row, normalized, "contactNote");
        putIfPresent(row, normalized, "country");
        putIfPresent(row, normalized, "email");
        putIfPresent(row, normalized, "enabled");
        putIfPresent(row, normalized, "facebook");
        putIfPresent(row, normalized, "gender");
        putIfPresent(row, normalized, "linkedin");
        putIfPresent(row, normalized, "mobile");
        putIfPresent(row, normalized, "name");
        putIfPresent(row, normalized, "note");
        putIfPresent(row, normalized, "password");
        putIfPresent(row, normalized, "secured");
        putIfPresent(row, normalized, "skype");
        putIfPresent(row, normalized, "surname");
        putIfPresent(row, normalized, "username");
        putIfPresent(row, normalized, "website");
        putIfPresent(row, normalized, "zipCode");

        ObjectNode objectNode = OBJECT_MAPPER.createObjectNode();

        // Strings
        for (String key : new String[]{
            "address", "address2", "birthDate", "city", "contactNote", "country",
            "email", "facebook", "gender", "linkedin", "mobile", "name", "note",
            "password", "skype", "surname", "username", "website", "zipCode"
        }) {
            if (normalized.containsKey(key)) {
                objectNode.put(key, normalized.get(key));
            }
        }

        // Booleans
        if (normalized.containsKey("enabled")) {
            objectNode.put("enabled", Boolean.parseBoolean(normalized.get("enabled")));
        }
        if (normalized.containsKey("secured")) {
            objectNode.put("secured", Boolean.parseBoolean(normalized.get("secured")));
        }

        // Add the ID as a path parameter
        Map<String, String> pathParameters = new HashMap<>();
        if (normalized.containsKey("id")) {
            pathParameters.put("id", normalized.get("id"));
        }
        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withBodyParameter(objectNode.toString())
                .withPathParameters(pathParameters);

        return b.build();
    }
}
