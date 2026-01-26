package mt.foursquare.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.*;

public class GetSearchMapper implements CsvRowMapper {

    private static final Properties P = CsvRowMapper.loadProps("foursquare.properties");
    private static final String DEFAULT_VERSION = "2025-06-17";
    private static final List<String> categories = Arrays.asList("fsq_place_id", "name", "categories", "location", "latitude", "longitude", "distance", "tel", "email", "website", "social_media", "link", "date_closed", "placemaker_url", "chains", "store_id", "related_places", "extended_location", "unresolved_flags");


    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> normalized = new HashMap<>();

        putIfPresent(row, normalized, "X-Places-Api-Version");
        putIfPresent(row, normalized, "query");
        putIfPresent(row, normalized, "ll");
        putIfPresent(row, normalized, "radius");
        putIfPresent(row, normalized, "fsq_category_ids");
        putIfPresent(row, normalized, "fsq_chain_ids");
        putIfPresent(row, normalized, "exclude_fsq_chain_ids");
        putIfPresent(row, normalized, "exclude_all_chains");
        putIfPresent(row, normalized, "fields");
        putIfPresent(row, normalized, "min_price");
        putIfPresent(row, normalized, "max_price");
        putIfPresent(row, normalized, "open_at");
        putIfPresent(row, normalized, "open_now");
        putIfPresent(row, normalized, "tel_format");
        putIfPresent(row, normalized, "ne");
        putIfPresent(row, normalized, "sw");
        putIfPresent(row, normalized, "near");
        putIfPresent(row, normalized, "sort");
        putIfPresent(row, normalized, "limit");

        Map<String, String> query = new LinkedHashMap<>();

        if (normalized.containsKey("query")) {
            query.put("query", normalized.get("query"));
        }
        if (normalized.containsKey("ll")) {
            query.put("ll", normalized.get("ll"));
        }
        if (normalized.containsKey("radius")) {
            query.put("radius", normalized.get("radius"));
        }
        if (normalized.containsKey("fsq_category_ids")) {
            query.put("fsq_category_ids", normalized.get("fsq_category_ids"));
        }
        if (normalized.containsKey("fsq_chain_ids")) {
            query.put("fsq_chain_ids", normalized.get("fsq_chain_ids"));
        }
        if (normalized.containsKey("exclude_fsq_chain_ids")) {
            query.put("exclude_fsq_chain_ids", normalized.get("exclude_fsq_chain_ids"));
        }
        if (normalized.containsKey("exclude_all_chains")) {
            query.put("exclude_all_chains", String.valueOf(Boolean.parseBoolean(normalized.get("exclude_all_chains"))));
        }
        if (normalized.containsKey("fields")) {
            int idx = Integer.parseInt(normalized.get("fields"));
            String fields = String.join(",", categories.subList(0, idx));
            query.put("fields", fields);
        }
        if (normalized.containsKey("min_price")) {
            query.put("min_price", normalized.get("min_price"));
        }
        if (normalized.containsKey("max_price")) {
            query.put("max_price", normalized.get("max_price"));
        }
        if (normalized.containsKey("open_at")) {
            query.put("open_at", normalized.get("open_at"));
        }
        if (normalized.containsKey("open_now")) {
            query.put("open_now", String.valueOf(Boolean.parseBoolean(normalized.get("open_now"))));
        }
        if (normalized.containsKey("tel_format")) {
            query.put("tel_format", normalized.get("tel_format"));
        }
        if (normalized.containsKey("ne")) {
            query.put("ne", normalized.get("ne"));
        }
        if (normalized.containsKey("sw")) {
            query.put("sw", normalized.get("sw"));
        }
        if (normalized.containsKey("near")) {
            query.put("near", normalized.get("near"));
        }
        if (normalized.containsKey("sort")) {
            query.put("sort", normalized.get("sort"));
        }
        if (normalized.containsKey("limit")) {
            query.put("limit", normalized.get("limit"));
        }

        LogRecord.Builder builder = new LogRecord.Builder().withPath(operationPath).withHttpMethod(httpMethod).withQueryParameters(query);

        Map<String, String> headers = new LinkedHashMap<>();
        if (normalized.containsKey("X-Places-Api-Version")) {
            headers.put("X-Places-Api-Version", normalized.get("X-Places-Api-Version"));
        }

        if (isAuthEnabled(row)) {
            String token = P.getProperty("foursquare.key");
            if (token == null || token.isEmpty()) {
                throw new IllegalStateException("Missing foursquare.key property");
            }
            headers.put("Authorization", "Bearer " + token);
        }

        if (!headers.isEmpty()) {
            builder.withRequestHeaders(headers);
        }

        return builder.build();
    }

    public static void main(String[] args) {
        Map<String, String> params = new LinkedHashMap<>();

        // Required header
        params.put("X-Places-Api-Version", "2025-06-17");

        // Basic query parameters
        params.put("query", "Cafe");

        // Location parameters
        params.put("ll", "40.41406,-3.70803");
        params.put("radius", "1000");
        params.put("ne", "68.099821,27.629948");
        params.put("sw", "-49.106476,-70.807550");
        params.put("near", "Madrid");

        // Category and chain filters
        params.put("fsq_category_ids", "63be6904847c3692a84b9bb6");
        params.put("fsq_chain_ids", "5568ecaaa7c8a9cf8ec38f1c");
        params.put("exclude_fsq_chain_ids", "556f3bfabd6a8104863beb14");
        params.put("exclude_all_chains", "false");

        // Field selector
        params.put("fields", "fsq_place_id,name,categories,location,latitude,longitude,distance,tel," + "email,website,social_media,link,date_closed,placemaker_url,chains,store_id," + "related_places,extended_location,unresolved_flags");

        // Price range
        params.put("min_price", "2");
        params.put("max_price", "4");

        // Opening hours
        params.put("open_at", "2T0701");
        params.put("open_now", "false");

        // Telephone format
        params.put("tel_format", "NATIONAL");

        // Sorting and limit
        params.put("sort", "POPULARITY");
        params.put("limit", "10");

        GetSearchMapper mapper = new GetSearchMapper();
        LogRecord r = mapper.map("/v1/place/search", "get", params);
        System.out.println(r);
    }
}
