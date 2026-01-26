package mt.market.mapper;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PutCustomerCartMapper implements CsvRowMapper {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private static final Map<String, String> USERS = Map.of(
            "ivan.petrov@yandex.ru", "petrov",
            "user2@yandex.ru", "yuridolgoruki"
    );

   /**
     * construct Basic Auth 
     *
     * @param userId   user 
     * @param password password
     * @return Authorization "Basic YWRtaW46cGFzc3dvcmQ="
     */
    private static String buildBasicAuthHeader(String userId, String password) {
        String raw = userId + ":" + password;
        String encoded = Base64.getEncoder()
                .encodeToString(raw.getBytes(StandardCharsets.UTF_8));
        return "Basic " + encoded;
    }

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "productId");
        putIfPresent(row, normalized, "quantity");
        putIfPresent(row, normalized, "user");

        ObjectNode objectNode = OBJECT_MAPPER.createObjectNode();
        if (normalized.containsKey("productId")) {
            objectNode.put("productId", Integer.parseInt(normalized.get("productId")));
        }
        if (normalized.containsKey("quantity")) {
            objectNode.put("quantity", Integer.parseInt(normalized.get("quantity")));
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withBodyParameter(objectNode.toString());

        if (isAuthEnabled(row)) {
            String userId = normalized.get("user");
            String password = USERS.get(userId);

            b.withRequestHeaders(Map.of("Authorization", buildBasicAuthHeader(userId, password)));
        }

        return b.build();
    }
}

