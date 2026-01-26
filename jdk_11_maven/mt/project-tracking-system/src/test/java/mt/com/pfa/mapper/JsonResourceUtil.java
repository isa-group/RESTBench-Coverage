package mt.com.pfa.mapper;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * Utility class for eagerly loading JSON array resources from the classpath.
 * All resources are loaded once at class initialization (single-threaded use only).
 */
public final class JsonResourceUtil {
    private static final ObjectMapper MAPPER = new ObjectMapper();
    // Eagerly loaded JSON arrays for all resource files
    private static final Map<String, ArrayNode> RESOURCES = new HashMap<>();

    static {
        String[] resourceFiles = {
            "employees.json",
            "projects.json",
            "departments.json",
            "credentials.json",
            "assignments.json"
        };
        for (String file : resourceFiles) {
            try (InputStream is = JsonResourceUtil.class
                    .getClassLoader()
                    .getResourceAsStream(file)) {
                if (is == null) {
                    throw new IllegalStateException(file + " not found in classpath");
                }
                ArrayNode array = (ArrayNode) MAPPER.readTree(is);
                RESOURCES.put(file, array);
            } catch (IOException e) {
                throw new RuntimeException("Failed to load JSON resource: " + file, e);
            }
        }
    }

    // Private constructor to prevent instantiation
    private JsonResourceUtil() { }

    /**
     * Returns the pre-loaded JSON array for the given resource name.
     * @param resourceName JSON filename (must be one of the loaded resources).
     * @return the ArrayNode parsed from the file.
     * @throws IllegalArgumentException if the resource name is unknown.
     */
    public static ArrayNode getArray(String resourceName) {
        ArrayNode node = RESOURCES.get(resourceName);
        if (node == null) {
            throw new IllegalArgumentException("Unknown JSON resource: " + resourceName);
        }
        return node;
    }

    /**
     * Finds a single object within a pre-loaded JSON array by matching a field's text value.
     * @param resourceName the filename of the JSON resource.
     * @param idField the JSON field name to match on (e.g., "employeeId").
     * @param idValue the text value to compare against.
     * @return the matching ObjectNode.
     * @throws IllegalArgumentException if no matching object is found.
     */
    public static ObjectNode findOne(String resourceName, String idField, String idValue) {
        ArrayNode array = getArray(resourceName);
        for (int i = 0, len = array.size(); i < len; i++) {
            ObjectNode node = (ObjectNode) array.get(i);
            if (node.has(idField) && node.get(idField).asText().equals(idValue)) {
                return node;
            }
        }
        throw new IllegalArgumentException(
                String.format("No entry in %s where %s=%s", resourceName, idField, idValue));
    }
}