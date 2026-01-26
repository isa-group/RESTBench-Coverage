package mt.com.pfa.mapper;

import java.util.HashMap;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

/**
 * CSV-to-LogRecord mapper for POST /assignments
 * Builds a JSON object of the assignment request body by
 * merging CSV values and embedding full employee/project nodes.
 */
public class PostAssignmentMapper implements CsvRowMapper {
    private static final ObjectMapper JSON_MAPPER = new ObjectMapper();

    @Override
    public LogRecord map(String path, String httpMethod, Map<String, String> csvRow) {
        Map<String, String> normalized = new HashMap<>();
        putIfPresent(csvRow, normalized, "employee");
        putIfPresent(csvRow, normalized, "employeeId");
        putIfPresent(csvRow, normalized, "project");
        putIfPresent(csvRow, normalized, "projectId");
        putIfPresent(csvRow, normalized, "commitDate");
        putIfPresent(csvRow, normalized, "commitEmpDesc");
        putIfPresent(csvRow, normalized, "commitMgrDesc");

        ObjectNode assignment = JSON_MAPPER.createObjectNode();
        if (normalized.containsKey("employeeId")) {
            assignment.put("employeeId", Integer.valueOf(normalized.get("employeeId")));
        }
        if (normalized.containsKey("projectId")) {
            assignment.put("projectId", Integer.valueOf(normalized.get("projectId")));
        }
        if (normalized.containsKey("commitDate")) {
            assignment.put("commitDate", normalized.get("commitDate"));
        }
        if (normalized.containsKey("commitEmpDesc")) {
            assignment.put("commitEmpDesc", normalized.get("commitEmpDesc"));
        }
        if (normalized.containsKey("commitMgrDesc")) {
            assignment.put("commitMgrDesc", normalized.get("commitMgrDesc"));
        }
        if (normalized.containsKey("employee")) {
            ObjectNode emp = JsonResourceUtil.findOne(
                    "employees.json", "employeeId", normalized.get("employee"));
            assignment.set("employee", emp);
        }
        if (normalized.containsKey("project")) {
            ObjectNode proj = JsonResourceUtil.findOne(
                    "projects.json", "projectId", normalized.get("project"));
            assignment.set("project", proj);
        }

        return new LogRecord.Builder()
                .withPath(path)
                .withHttpMethod(httpMethod)
                .withBodyParameter(assignment)
                .build();
    }
}