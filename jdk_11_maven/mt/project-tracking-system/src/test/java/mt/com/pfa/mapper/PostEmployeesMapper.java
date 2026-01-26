package mt.com.pfa.mapper;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PostEmployeesMapper implements CsvRowMapper {
    private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(PostEmployeesMapper.class);
    
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private static final List<ObjectNode> CREDENTIALS = new ArrayList<>();
    
    static {
        ObjectNode obj1 = MAPPER.createObjectNode();
        obj1.put("credentialId", 1);
        obj1.put("username", "imentouk");
        obj1.put("password", "password111");
        obj1.put("enabled", true);
        obj1.put("role", "EMP");

        ObjectNode obj2 = MAPPER.createObjectNode();
        obj2.put("credentialId", 2);
        obj2.put("username", "admin");
        obj2.put("password", "password222");
        obj2.put("enabled", true);
        obj2.put("role", "ROLE_EMP");

        ObjectNode obj3 = MAPPER.createObjectNode();
        obj3.put("username", "admin");
        obj3.put("password", "password222");
        obj3.put("enabled", true);
        obj3.put("role", "ROLE_EMP");

        CREDENTIALS.add(obj1);
        CREDENTIALS.add(obj2);
        CREDENTIALS.add(obj3);
    }


    @Override
    public LogRecord map(String path, String httpMethod, Map<String, String> csvRow) {
        Map<String, String> normalized = new HashMap<>();
        putIfPresent(csvRow, normalized, "employeeId");
        putIfPresent(csvRow, normalized, "firstName");
        putIfPresent(csvRow, normalized, "lastName");
        putIfPresent(csvRow, normalized, "email");
        putIfPresent(csvRow, normalized, "phone");
        putIfPresent(csvRow, normalized, "hiredate");
        putIfPresent(csvRow, normalized, "job");
        putIfPresent(csvRow, normalized, "salary");
        putIfPresent(csvRow, normalized, "manager");
        putIfPresent(csvRow, normalized, "department");
        putIfPresent(csvRow, normalized, "credential");

        ObjectNode employee = MAPPER.createObjectNode();
        if (normalized.containsKey("employeeId")) {
            employee.put("employeeId", Integer.valueOf(normalized.get("employeeId")));
        }
        if (normalized.containsKey("firstName")) {
            employee.put("firstName", normalized.get("firstName"));
        }
        if (normalized.containsKey("lastName")) {
            employee.put("lastName", normalized.get("lastName"));
        }
        if (normalized.containsKey("email")) {
            employee.put("email", normalized.get("email"));
        }
        if (normalized.containsKey("phone")) {
            employee.put("phone", normalized.get("phone"));
        }
        if (normalized.containsKey("hiredate")) {
            employee.put("hiredate", normalized.get("hiredate"));
        }
        if (normalized.containsKey("job")) {
            employee.put("job", normalized.get("job"));
        }
        if (normalized.containsKey("salary")) {
            employee.put("salary", Double.valueOf(normalized.get("salary")));
        }
        if (normalized.containsKey("manager")) {
            ObjectNode mgr = JsonResourceUtil.findOne(
                    "employees.json", "employeeId", normalized.get("manager"));
            employee.set("manager", mgr);
        }
        if (normalized.containsKey("department")) {
            ObjectNode dept = JsonResourceUtil.findOne(
                    "departments.json", "departmentId", normalized.get("department"));
            employee.set("department", dept);
        }
        if (normalized.containsKey("credential")) {
            logger.info("Normalized: {}", normalized);
            Integer credentialId = Integer.valueOf(normalized.get("credential"));
            employee.set("credential", CREDENTIALS.get(credentialId - 1));
            logger.info("Credential set: {}", CREDENTIALS.get(credentialId - 1));
        }

        return new LogRecord.Builder()
                .withPath(path)
                .withHttpMethod(httpMethod)
                .withBodyParameter(employee)
                .build();
    }
}
