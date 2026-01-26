package mt.org.languagetool.server.mapper;

import java.util.LinkedHashMap;
import java.util.Map;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class PostCheckCsvRowMapper implements CsvRowMapper {
    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> params = new LinkedHashMap<>();

        // Required
        putIfPresent(row, params, "language");

        // Optional form parameters
        putIfPresent(row, params, "text");
        putIfPresent(row, params, "data");
        putIfPresent(row, params, "altLanguages");
        putIfPresent(row, params, "motherTongue");
        putIfPresent(row, params, "preferredVariants");
        putIfPresent(row, params, "enabledRules");
        putIfPresent(row, params, "disabledRules");
        putIfPresent(row, params, "enabledCategories");
        putIfPresent(row, params, "disabledCategories");

        // Boolean flag
        putIfPresent(row, params, "enabledOnly");

        // Build and return the LogRecord
        return LogRecord.builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withFormParameters(params)
                .build();
    }

}
