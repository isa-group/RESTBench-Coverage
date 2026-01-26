package mt.org.languagetool.server.mapper;

import java.util.Map;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

public class GetLanguageCsvRowMapper implements CsvRowMapper {
    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        return LogRecord.builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .build();
    }
}
