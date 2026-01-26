package mt.se.devscout.scoutapi.mapper;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PostActivitiesMapper implements CsvRowMapper {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private static List<ArrayNode> TAGS = new ArrayList<>();
    private static List<ArrayNode> MEDIA_FILES = new ArrayList<>();

    static {
        // {
        // "group": "1feelings",
        // "name": "H1appy",
        // "media_file": null,
        // "activities_count": 1
        // }
        ArrayNode tagArray1 = OBJECT_MAPPER.createArrayNode();
        ObjectNode tag1 = OBJECT_MAPPER.createObjectNode();
        tag1.put("group", "1feelings");
        tag1.put("name", "1Happy");
        tag1.put("activities_count", 1);
        tagArray1.add(tag1);
        TAGS.add(tagArray1);
        ArrayNode tagArray2 = OBJECT_MAPPER.createArrayNode();
        ObjectNode tag2 = OBJECT_MAPPER.createObjectNode();
        tag2.put("id", 4);
        tagArray2.add(tag2);
        TAGS.add(tagArray2);

        //{
        // "uri": "https://example.com/forest.jpg",
        // "mime_type": "image/jpeg",
        // "name": "forest hunt"
        // }
        ArrayNode mediaFileArray1 = OBJECT_MAPPER.createArrayNode();
        ObjectNode mediaFile1 = OBJECT_MAPPER.createObjectNode();
        mediaFile1.put("uri", "https://example.com/forest.jpg");
        mediaFile1.put("mime_type", "image/jpeg");
        mediaFile1.put("name", "forest hunt");
        mediaFileArray1.add(mediaFile1);
        MEDIA_FILES.add(mediaFileArray1);

    }

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "id");
        putIfPresent(row, normalized, "name");
        putIfPresent(row, normalized, "date_published");
        putIfPresent(row, normalized, "date_updated");
        putIfPresent(row, normalized, "date_created");
        putIfPresent(row, normalized, "description_material");
        putIfPresent(row, normalized, "description_introduction");
        putIfPresent(row, normalized, "description_prepare");
        putIfPresent(row, normalized, "description_main");
        putIfPresent(row, normalized, "description_safety");
        putIfPresent(row, normalized, "description_notes");
        putIfPresent(row, normalized, "age_min");
        putIfPresent(row, normalized, "age_max");
        putIfPresent(row, normalized, "participants_min");
        putIfPresent(row, normalized, "participants_max");
        putIfPresent(row, normalized, "time_min");
        putIfPresent(row, normalized, "time_max");
        putIfPresent(row, normalized, "featured");
        putIfPresent(row, normalized, "tags");
        putIfPresent(row, normalized, "source");
        putIfPresent(row, normalized, "author");
        putIfPresent(row, normalized, "media_files");
        putIfPresent(row, normalized, "author");

        ObjectNode objectNode = OBJECT_MAPPER.createObjectNode();
        if (normalized.containsKey("id")) {
            objectNode.put("id", Long.parseLong(normalized.get("id")));
        }
        if (normalized.containsKey("name")) {
            objectNode.put("name", normalized.get("name"));
        }
        if (normalized.containsKey("date_published")) {
            objectNode.put("date_published", normalized.get("date_published"));
        }
        if (normalized.containsKey("date_updated")) {
            objectNode.put("date_updated", normalized.get("date_updated"));
        }
        if (normalized.containsKey("date_created")) {
            objectNode.put("date_created", normalized.get("date_created"));
        }
        if (normalized.containsKey("description_material")) {
            objectNode.put("description_material", normalized.get("description_material"));
        }
        if (normalized.containsKey("description_introduction")) {
            objectNode.put("description_introduction", normalized.get("description_introduction"));
        }
        if (normalized.containsKey("description_prepare")) {
            objectNode.put("description_prepare", normalized.get("description_prepare"));
        }
        if (normalized.containsKey("description_main")) {
            objectNode.put("description_main", normalized.get("description_main"));
        }
        if (normalized.containsKey("description_safety")) {
            objectNode.put("description_safety", normalized.get("description_safety"));
        }
        if (normalized.containsKey("description_notes")) {
            objectNode.put("description_notes", normalized.get("description_notes"));
        }
        if (normalized.containsKey("age_min")) {
            objectNode.put("age_min", Integer.parseInt(normalized.get("age_min")));
        }
        if (normalized.containsKey("age_max")) {
            objectNode.put("age_max", Integer.parseInt(normalized.get("age_max")));
        }
        if (normalized.containsKey("participants_min")) {
            objectNode.put("participants_min", Integer.parseInt(normalized.get("participants_min")));
        }
        if (normalized.containsKey("participants_max")) {
            objectNode.put("participants_max", Integer.parseInt(normalized.get("participants_max")));
        }
        if (normalized.containsKey("time_min")) {
            objectNode.put("time_min", Integer.parseInt(normalized.get("time_min")));
        }
        if (normalized.containsKey("time_max")) {
            objectNode.put("time_max", Integer.parseInt(normalized.get("time_max")));
        }
        if (normalized.containsKey("featured")) {
            objectNode.put("featured", Boolean.parseBoolean(normalized.get("featured")));
        }
        if (normalized.containsKey("tags")) {
            Integer tagIndex = Integer.parseInt(normalized.get("tags"));
            objectNode.set("tags", TAGS.get(tagIndex - 1));
        }
        if (normalized.containsKey("source")) {
            objectNode.put("source", normalized.get("source"));
        }
        if (normalized.containsKey("author")) {
            objectNode.put("author", normalized.get("author"));
        }
        if (normalized.containsKey("media_files")) {
            Integer mediaFileIndex = Integer.parseInt(normalized.get("media_files"));
            objectNode.set("media_files", MEDIA_FILES.get(mediaFileIndex - 1));
        }
        if (normalized.containsKey("author")) {
            ObjectNode authorNode = OBJECT_MAPPER.createObjectNode();
            authorNode.put("id", Integer.parseInt(normalized.get("author")));
            objectNode.set("author", authorNode);
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
