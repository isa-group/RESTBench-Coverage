package mt.stripe.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.Collectors;

public class PostProductMapper implements CsvRowMapper {

    private static final List<String> TAX_CODES = loadResource("product_tax_codes.csv");
    private static final List<String> CURRENCIES = loadResource("iso_currency_codes.csv");
    private static final Properties p = CsvRowMapper.loadProps("stripe.properties");

    @Override
    public LogRecord map(String operationPath, String httpMethod, Map<String, String> row) {
        // Collect only present inputs from the CSV row (trimmed, non-empty)
        Map<String, String> n = new HashMap<>();
        putIfPresent(row, n, "name");
        putIfPresent(row, n, "active");
        putIfPresent(row, n, "description");
        putIfPresent(row, n, "id");
        putIfPresent(row, n, "taxCode");
        putIfPresent(row, n, "currency");
        putIfPresent(row, n, "recurringInterval");
        putIfPresent(row, n, "recurringIntervalCount");
        putIfPresent(row, n, "taxBehavior");
        putIfPresent(row, n, "unitAmount");
        putIfPresent(row, n, "unitAmountDecimal");
        putIfPresent(row, n, "customEnabled");
        putIfPresent(row, n, "customMaximum");
        putIfPresent(row, n, "customMinimum");
        putIfPresent(row, n, "customPreset");
        putIfPresent(row, n, "images");
        putIfPresent(row, n, "marketingFeatures");
        putIfPresent(row, n, "packageHeight");
        putIfPresent(row, n, "packageLength");
        putIfPresent(row, n, "packageWeight");
        putIfPresent(row, n, "packageWidth");
        putIfPresent(row, n, "shippable");
        putIfPresent(row, n, "stateDescr");
        putIfPresent(row, n, "unitLabel");
        putIfPresent(row, n, "url");

        // Build x-www-form-urlencoded parameters with bracket notation (mainstream)
        Map<String, String> form = new LinkedHashMap<>();

        // ---- Top-level product fields ----
        if (n.containsKey("name")) {
            form.put("name", resolveName(n.get("name")));
        }
        if (n.containsKey("active")) {
            form.put("active", String.valueOf(Boolean.parseBoolean(n.get("active"))));
        }
        if (n.containsKey("description")) {
            form.put("description", n.get("description"));
        }
        if (n.containsKey("id")) {
            form.put("id", resolveId(n.get("id")));
        }
        if (n.containsKey("taxCode")) {
            form.put("tax_code", resolveTaxCode(n.get("taxCode")));
        }

        // ---- default_price_data (bracket notation) ----
        if (n.containsKey("currency")) {
            form.put("default_price_data[currency]", resolveCurrency(n.get("currency")));
        }

        if (n.containsKey("taxBehavior")) {
            String tb = n.get("taxBehavior");
            form.put("default_price_data[tax_behavior]", tb);
        }

        boolean hasDecimal = n.containsKey("unitAmountDecimal");
        boolean hasInteger = n.containsKey("unitAmount");

        boolean hasCustom =
                n.containsKey("customEnabled") ||
                        n.containsKey("customMaximum") ||
                        n.containsKey("customMinimum") ||
                        n.containsKey("customPreset");

        if (hasDecimal) {
            // validate decimal
            requireDecimal(n.get("unitAmountDecimal"), "unitAmountDecimal");
            form.put("default_price_data[unit_amount_decimal]", n.get("unitAmountDecimal"));
        }
        if (hasInteger) {
            // validate integer
            requireInteger(n.get("unitAmount"), "unitAmount");
            form.put("default_price_data[unit_amount]", n.get("unitAmount"));
        }
        if (hasCustom) {
            // custom_unit_amount subtree
            if (n.containsKey("customEnabled")) {
                form.put("default_price_data[custom_unit_amount][enabled]",
                        String.valueOf(Boolean.parseBoolean(n.get("customEnabled"))));
            }
            if (n.containsKey("customMaximum")) {
                requireInteger(n.get("customMaximum"), "customMaximum");
                form.put("default_price_data[custom_unit_amount][maximum]", n.get("customMaximum"));
            }
            if (n.containsKey("customMinimum")) {
                requireInteger(n.get("customMinimum"), "customMinimum");
                form.put("default_price_data[custom_unit_amount][minimum]", n.get("customMinimum"));
            }
            if (n.containsKey("customPreset")) {
                requireInteger(n.get("customPreset"), "customPreset");
                form.put("default_price_data[custom_unit_amount][preset]", n.get("customPreset"));
            }
        }

        // recurring subtree
        if (n.containsKey("recurringInterval")) {
            form.put("default_price_data[recurring][interval]", n.get("recurringInterval"));
        }
        if (n.containsKey("recurringIntervalCount")) {
            requireInteger(n.get("recurringIntervalCount"), "recurringIntervalCount");
            form.put("default_price_data[recurring][interval_count]", n.get("recurringIntervalCount"));
        }

        // ---- arrays ----
        // images: generate images[0], images[1], ...
        if (n.containsKey("images")) {
            int count = requireNonNegativeInt(n.get("images"), "images");
            for (int i = 0; i < Math.min(count, 8); i++) {
                form.put("images[" + i + "]", "https://cdn.stripe.test/images/" + i);
            }
        }

        // marketing_features: marketing_features[0][name] = "Feature-xxx"
        if (n.containsKey("marketingFeatures")) {
            int count = requireNonNegativeInt(n.get("marketingFeatures"), "marketingFeatures");
            for (int i = 0; i < Math.min(count, 15); i++) {
                form.put("marketing_features[" + i + "][name]", "Feature-" + i);
            }
        }

        // ---- package_dimensions ----
        if (n.containsKey("packageHeight")) {
            requireDecimal(n.get("packageHeight"), "packageHeight");
            form.put("package_dimensions[height]", n.get("packageHeight"));
        }
        if (n.containsKey("packageLength")) {
            requireDecimal(n.get("packageLength"), "packageLength");
            form.put("package_dimensions[length]", n.get("packageLength"));
        }
        if (n.containsKey("packageWeight")) {
            requireDecimal(n.get("packageWeight"), "packageWeight");
            form.put("package_dimensions[weight]", n.get("packageWeight"));
        }
        if (n.containsKey("packageWidth")) {
            requireDecimal(n.get("packageWidth"), "packageWidth");
            form.put("package_dimensions[width]", n.get("packageWidth"));
        }

        // ---- misc ----
        if (n.containsKey("shippable")) {
            form.put("shippable", String.valueOf(Boolean.parseBoolean(n.get("shippable"))));
        }
        if (n.containsKey("stateDescr")) {
            form.put("statement_descriptor", n.get("stateDescr"));
        }
        if (n.containsKey("unitLabel")) {
            form.put("unit_label", n.get("unitLabel"));
        }
        if (n.containsKey("url")) {
            form.put("url", n.get("url"));
        }

        LogRecord.Builder b =  new LogRecord.Builder()
                .withPath(operationPath)
                .withHttpMethod(httpMethod)
                .withFormParameters(form); // mainstream: form params with bracket notation

        if (isAuthEnabled(row)) {
            Map<String, String> headers = new HashMap<>();
            String secret = p.getProperty("stripe.key");
            headers.put("Authorization", "Bearer " + secret);
            b.withRequestHeaders(headers);
        }

        return b.build();
    }

    private static void requireDecimal(String raw, String field) {
        try {
            new BigDecimal(raw);
        } catch (Exception ex) {
            throw new IllegalArgumentException("Invalid decimal for " + field + ": " + raw, ex);
        }
    }

    private static void requireInteger(String raw, String field) {
        try {
            Integer.parseInt(raw);
        } catch (Exception ex) {
            throw new IllegalArgumentException("Invalid integer for " + field + ": " + raw, ex);
        }
    }

    private static int requireNonNegativeInt(String raw, String field) {
        try {
            int v = Integer.parseInt(raw);
            if (v < 0) throw new IllegalArgumentException();
            return v;
        } catch (Exception ex) {
            throw new IllegalArgumentException("Invalid non-negative integer for " + field + ": " + raw, ex);
        }
    }

    private static String resolveName(String value) {
        if ("1".equals(value)) return "Product-" + randomToken(12);
        return value;
    }

    private static String resolveId(String value) {
        if ("1".equals(value)) return "prod_" + randomToken(14);
        return value;
    }

    private static String resolveTaxCode(String raw) {
        int index = Integer.parseInt(raw);
        if (index < 0 || index >= TAX_CODES.size()) {
            throw new IllegalArgumentException("taxCode index out of range: " + index);
        }
        return TAX_CODES.get(index);
    }

    private static String resolveCurrency(String raw) {
        int index = Integer.parseInt(raw);
        if (index < 0 || index >= CURRENCIES.size()) {
            throw new IllegalArgumentException("currency index out of range: " + index);
        }
        // ISO-4217 code expected in lowercase
        return CURRENCIES.get(index).toLowerCase();
    }

    private static List<String> loadResource(String resourceName) {
        try (InputStream inputStream = PostProductMapper.class.getResourceAsStream("/" + resourceName)) {
            if (inputStream == null) {
                throw new IllegalStateException("Resource not found: " + resourceName);
            }
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {
                List<String> values = new ArrayList<>();
                String line;
                while ((line = reader.readLine()) != null) {
                    String cleaned = stripBom(line).trim();
                    if (!cleaned.isEmpty()) {
                        values.add(stripQuotes(cleaned));
                    }
                }
                return values;
            }
        } catch (IOException e) {
            throw new IllegalStateException("Failed to load resource: " + resourceName, e);
        }
    }

    private static String stripQuotes(String value) {
        if (value.startsWith("\"") && value.endsWith("\"") && value.length() >= 2) {
            return value.substring(1, value.length() - 1);
        }
        return value;
    }

    private static String stripBom(String value) {
        if (value != null && !value.isEmpty() && value.charAt(0) == '\uFEFF') {
            return value.substring(1);
        }
        return value;
    }

    private static String randomToken(int length) {
        String token = UUID.randomUUID().toString().replace("-", "");
        return (length >= token.length()) ? token : token.substring(0, length);
    }

    // Quick manual check (prints the LogRecord)
    public static void main(String[] args) {
        Map<String, String> row = new HashMap<>();

        // ---- Product-level fields (all non-null) ----
        // name: "1" triggers random name generation in resolveName()
        row.put("name", "1");
        // active: choose "true" among true/false/NULL
        row.put("active", "true");
        // description: use medium-length description
        row.put("description", "desc_medium");
        // id: "1" triggers random ID generation in resolveId()
        row.put("id", "1");
        // taxCode: valid index (0–639)
        row.put("taxCode", "5");

        // Images and marketing features: choose positive integers
        row.put("images", "3");              // valid range: 1–8
        row.put("marketingFeatures", "4");   // valid range: 1–15

        // Package dimensions (decimal values)
        row.put("packageHeight", "5.5");
        row.put("packageLength", "6.4");
        row.put("packageWeight", "3.5");
        row.put("packageWidth",  "4.0");

        // Other top-level attributes
        row.put("shippable", "true");
        row.put("stateDescr", "sd_label");
        row.put("unitLabel", "license");
        row.put("url", "https://example.com/p");

        // ---- default_price_data fields (all non-null) ----
        // currency: index (0–133)
        row.put("currency", "10");

        // taxBehavior: choose "exclusive" (among exclusive/inclusive/unspecified)
        row.put("taxBehavior", "exclusive");
        // add alternate snake_case key to match current implementation
        row.put("tax_behavior", "exclusive");

        // unitAmount: integer value
        row.put("unitAmount", "9999");

        // unitAmountDecimal: decimal value (both camelCase and snake_case)
        row.put("unitAmountDecimal", "250.2");
        row.put("unit_amount_decimal", "250.2");

        // recurring data
        row.put("recurringInterval", "month"); // valid: day/week/month/year
        row.put("recurringIntervalCount", "3"); // valid: 1/3/12

        // custom_unit_amount data
        row.put("customEnabled", "true");
        row.put("customMaximum", "5000");
        row.put("customMinimum", "50");
        row.put("customPreset",  "200");

        PostProductMapper mapper = new PostProductMapper();
        LogRecord record = mapper.map("/products", "POST", row);
        System.out.println(record);
    }
}
