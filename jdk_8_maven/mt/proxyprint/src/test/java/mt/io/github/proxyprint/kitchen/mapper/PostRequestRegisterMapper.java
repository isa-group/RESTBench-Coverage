package mt.io.github.proxyprint.kitchen.mapper;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.HashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;

public class PostRequestRegisterMapper implements CsvRowMapper {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "managerName");
        putIfPresent(row, normalized, "managerUsername");
        putIfPresent(row, normalized, "managerEmail");
        putIfPresent(row, normalized, "managerPassword");

        putIfPresent(row, normalized, "pShopAddress");
        putIfPresent(row, normalized, "pShopLatitude");
        putIfPresent(row, normalized, "pShopLongitude");
        putIfPresent(row, normalized, "pShopNIF");
        putIfPresent(row, normalized, "pShopName");

        putIfPresent(row, normalized, "accepted");
        putIfPresent(row, normalized, "pShopDateRequestAccepted");

        ObjectNode objectNode = OBJECT_MAPPER.createObjectNode();

        if (normalized.containsKey("managerName")) {
            objectNode.put("managerName", normalized.get("managerName"));
        }

        if (normalized.containsKey("managerUsername")) {
            objectNode.put("managerUsername", normalized.get("managerUsername"));
        }

        if (normalized.containsKey("managerEmail")) {
            objectNode.put("managerEmail", normalized.get("managerEmail"));
        }

        if (normalized.containsKey("managerPassword")) {
            objectNode.put("managerPassword", normalized.get("managerPassword"));
        }

        if (normalized.containsKey("pShopAddress")) {
            objectNode.put("pShopAddress", normalized.get("pShopAddress"));
        }

        if (normalized.containsKey("pShopLatitude")) {
            objectNode.put("pShopLatitude", Double.parseDouble(normalized.get("pShopLatitude")));
        }

        if (normalized.containsKey("pShopLongitude")) {
            objectNode.put("pShopLongitude", Double.parseDouble(normalized.get("pShopLongitude")));
        }

        if (normalized.containsKey("pShopNIF")) {
            objectNode.put("pShopNIF", normalized.get("pShopNIF"));
        }

        if (normalized.containsKey("pShopName")) {
            objectNode.put("pShopName", normalized.get("pShopName"));
        }

        if (normalized.containsKey("accepted")) {
            objectNode.put("accepted", Boolean.parseBoolean(normalized.get("accepted")));
        }

        if (normalized.containsKey("pShopDateRequestAccepted")) {
            objectNode.put("pShopDateRequestAccepted", normalized.get("pShopDateRequestAccepted"));
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withBodyParameter(objectNode);

        return b.build();
    }
}
