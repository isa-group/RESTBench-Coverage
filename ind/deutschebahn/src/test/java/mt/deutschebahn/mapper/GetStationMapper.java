package mt.deutschebahn.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.*;

public class GetStationMapper implements CsvRowMapper {
    private final static Properties P = CsvRowMapper.loadProps("dustchebahn.properties");

    public static final List<String> SEARCH_GROUPS = Arrays.asList(
            // Group 1
            "Berlin Hauptbahnhof,Hamburg Hbf,Köln Hbf,Frankfurt (Main) Hbf,München Hbf,Stuttgart Hbf,Leipzig Hbf,Hannover Hbf,Düsseldorf Flughafen,Frankfurt am Main Flughafen Fernbahnhof",

            // Group 2
            "Heidelberg Hbf,Potsdam Hbf,Wiesbaden Hbf,Dresden Hbf,Aachen Hbf,Bremen Hbf,Lübeck Hbf,Nürnberg Hbf,Karlsruhe Hbf,Konstanz",

            // Group 3
            "Dortmund-Hörde,Reichenbach (Fils),Königs Wusterhausen,Düsseldorf-Eller Mitte,Wuppertal-Vohwinkel,Röthenbach (Pegnitz),Fürth (Odenw),Möhringen (b Tuttlingen),Schwarzenbach (Saale)"
    );

    public static final List<String> FEDERALSTATE_GROUPS = Arrays.asList(
            // Group 1
            "Nordrhein-Westfalen,Bayern,Baden-Württemberg,Niedersachsen,Hessen,Sachsen,Berlin,Rheinland-Pfalz,Schleswig-Holstein",

            // Group 2
            "Sachsen,Sachsen-Anhalt,Thüringen,Brandenburg,Mecklenburg-Vorpommern,Berlin,Hamburg,Bremen,Schleswig-Holstein",

            // Group 3
            "Bayern,Baden-Württemberg,Hessen,Rheinland-Pfalz,Saarland,Nordrhein-Westfalen,Thüringen,Niedersachsen"
    );

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> n = new HashMap<>();

        // parameters: offset, limit, searchstring, category, federalstate, eva, ril, logicaloperator
        putIfPresent(row, n, "offset");
        putIfPresent(row, n, "limit");
        putIfPresent(row, n, "searchstring");
        putIfPresent(row, n, "category");
        putIfPresent(row, n, "federalstate");
        putIfPresent(row, n, "eva");
        putIfPresent(row, n, "ril");
        putIfPresent(row, n, "logicaloperator");

        Map<String, String> queryParams = new HashMap<>();
        if (n.containsKey("offset")) {
            queryParams.put("offset", n.get("offset"));
        }
        if (n.containsKey("limit")) {
            queryParams.put("limit", n.get("limit"));
        }
        if (n.containsKey("searchstring")) {
            int idx = Integer.parseInt(n.get("searchstring"));
            if (idx < 0 || idx >= SEARCH_GROUPS.size()) {
                throw new IllegalArgumentException("searchstring index out of range: " + idx);
            }
            queryParams.put("searchstring", SEARCH_GROUPS.get(idx));
        }
        if (n.containsKey("category")) {
            queryParams.put("category", n.get("category"));
        }
        if (n.containsKey("federalstate")) {
            int idx = Integer.parseInt(n.get("federalstate"));
            if (idx < 0 || idx >= FEDERALSTATE_GROUPS.size()) {
                throw new IllegalArgumentException("federalstate index out of range: " + idx);
            }
            queryParams.put("federalstate", FEDERALSTATE_GROUPS.get(idx));
        }
        if (n.containsKey("eva")) {
            queryParams.put("eva", n.get("eva"));
        }
        if (n.containsKey("ril")) {
            queryParams.put("ril", n.get("ril"));
        }
        if (n.containsKey("logicaloperator")) {
            queryParams.put("logicaloperator", n.get("logicaloperator"));
        }
        LogRecord.Builder b = new LogRecord.Builder().withPath(operationPath).withHttpMethod(httpMethod).withQueryParameters(queryParams);

        if (isAuthEnabled(row)) {
            addAuth(b);
        }
        return b.build();
    }

    @Override
    public void addAuth(LogRecord.Builder b) {
        b.authApiKeyHeader("DB-Api-Key", P.getProperty("deutschebahn.clientSecret"));
        b.authApiKeyHeader("DB-Client-ID", P.getProperty("deutschebahn.clientId"));
    }
}
