package mt.amadeus.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;
import mt.amadeus.AmadeusTokenProvider;

import java.io.IOException;
import java.util.*;
import java.util.Properties;
import java.util.stream.Collectors;

public class HotelOffersMapper implements CsvRowMapper {
    private final static AmadeusTokenProvider TOKEN_PROVIDER;

    static {
        Properties p;
        p = CsvRowMapper.loadProps("amadeus.properties");
        TOKEN_PROVIDER = new AmadeusTokenProvider(p);
    }

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        Map<String, String> n = new HashMap<>();
        // ---- 必填 & 可选查询参数（Swagger 2.0: GET /v3/shopping/hotel-offers）----
        putIfPresent(row, n, "hotelIds");            // array, join by comma
        putIfPresent(row, n, "adults");              // required: integer 1..9
        putIfPresent(row, n, "checkInDate");         // YYYY-MM-DD
        putIfPresent(row, n, "checkOutDate");        // YYYY-MM-DD
        putIfPresent(row, n, "countryOfResidence");  // [A-Z]{2}
        putIfPresent(row, n, "roomQuantity");        // int 1..9
        putIfPresent(row, n, "priceRange");          // string interval
        putIfPresent(row, n, "currency");            // ^[A-Z]{3}$
        putIfPresent(row, n, "paymentPolicy");       // GUARANTEE/DEPOSIT/NONE
        putIfPresent(row, n, "boardType");           // ROOM_ONLY/.../ALL_INCLUSIVE
        putIfPresent(row, n, "includeClosed");       // boolean
        putIfPresent(row, n, "bestRateOnly");        // boolean, default true
        putIfPresent(row, n, "lang");                // ^[a-zA-Z0-9-]{2,5}$

        Map<String, String> queryParams = new LinkedHashMap<>();

        if (n.containsKey("hotelIds")) {
            queryParams.put("hotelIds", n.get("hotelIds"));
        }
        if (n.containsKey("adults")) {
            queryParams.put("adults", n.get("adults"));
        }
        if (n.containsKey("checkInDate")) {
            queryParams.put("checkInDate", n.get("checkInDate"));
        }
        if (n.containsKey("checkOutDate")) {
            queryParams.put("checkOutDate", n.get("checkOutDate"));
        }
        if (n.containsKey("countryOfResidence")) {
            queryParams.put("countryOfResidence", n.get("countryOfResidence"));
        }
        if (n.containsKey("roomQuantity")) {
            queryParams.put("roomQuantity", n.get("roomQuantity"));
        }
        if (n.containsKey("priceRange")) {
            queryParams.put("priceRange", n.get("priceRange"));
        }
        if (n.containsKey("currency")) {
            queryParams.put("currency", n.get("currency"));
        }
        if (n.containsKey("paymentPolicy")) {
            queryParams.put("paymentPolicy", n.get("paymentPolicy"));
        }
        if (n.containsKey("boardType")) {
            queryParams.put("boardType", n.get("boardType"));
        }
        if (n.containsKey("includeClosed")) {
            queryParams.put("includeClosed", n.get("includeClosed"));
        }
        if (n.containsKey("bestRateOnly")) {
            queryParams.put("bestRateOnly", n.get("bestRateOnly"));
        }
        if (n.containsKey("lang")) {
            queryParams.put("lang", n.get("lang"));
        }

        LogRecord.Builder b = new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams);

        if (isAuthEnabled(row)) {
            addAuth(b);
        }

        return b.build();
    }

    @Override
    public void addAuth(LogRecord.Builder b) {
        String token;
        try {
            token = TOKEN_PROVIDER.getAccessToken();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        b.authBearer(token);
    }
}