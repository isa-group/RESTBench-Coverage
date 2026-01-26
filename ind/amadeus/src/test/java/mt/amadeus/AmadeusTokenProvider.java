package mt.amadeus;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Properties;

/**
 * Token provider for Amadeus Self-Service API.
 * - Caches access_token until (now >= issuedAt + expires_in - clockSkew)
 * - Reads client_id/client_secret from a .properties file
 * - JDK 8, no extra HTTP libs
 */
public class AmadeusTokenProvider {

    private static final String DEFAULT_TOKEN_URL =
            "https://test.api.amadeus.com/v1/security/oauth2/token";
    private static final int DEFAULT_SKEW_SECONDS = 30;
    private static final ObjectMapper MAPPER = new ObjectMapper();

    private final String tokenUrl;
    private final String clientId;
    private final String clientSecret;
    private final int clockSkewSeconds;

    private String accessToken;              // cached token
    private long   expiresAtEpochMillis;     // absolute expiry time (with skew)

    public AmadeusTokenProvider(Properties props) {
        this.clientId = required(props, "amadeus.client_id");
        this.clientSecret = required(props, "amadeus.client_secret");
        this.tokenUrl = props.getProperty("amadeus.token_url", DEFAULT_TOKEN_URL);
        this.clockSkewSeconds = parseInt(props.getProperty("amadeus.clock_skew_seconds"),
                DEFAULT_SKEW_SECONDS);
    }

    /** Returns a valid token; refreshes if none or expired.  */
    public String getAccessToken() throws IOException {
        long now = System.currentTimeMillis();
        if (accessToken != null && now < expiresAtEpochMillis) {
            return accessToken;
        }
        refreshToken();
        return accessToken;
    }

    private void refreshToken() throws IOException {
        String body = "grant_type=" + enc("client_credentials")
                + "&client_id=" + enc(clientId)
                + "&client_secret=" + enc(clientSecret);

        HttpURLConnection conn = (HttpURLConnection) new URL(tokenUrl).openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setConnectTimeout(15000);
        conn.setReadTimeout(20000);
        conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");

        try (OutputStream os = conn.getOutputStream()) {
            os.write(body.getBytes(StandardCharsets.UTF_8));
        }

        int code = conn.getResponseCode();
        InputStream is = (code >= 200 && code < 300) ? conn.getInputStream() : conn.getErrorStream();
        String resp = readAll(is);

        if (code < 200 || code >= 300) {
            throw new IOException("Token request failed: HTTP " + code + " -> " + resp);
        }

        JsonNode root = MAPPER.readTree(resp);
        String tokenType = text(root, "token_type");      // "Bearer"
        String token     = text(root, "access_token");
        int    expiresIn = intVal(root, "expires_in", 1799);

        if (token == null || token.isEmpty()) {
            throw new IOException("Missing access_token in response: " + resp);
        }

        long nowMs = System.currentTimeMillis();
        long effective = Math.max(1, expiresIn - clockSkewSeconds) * 1000L;
        this.accessToken = token; // tokenType
        this.expiresAtEpochMillis = nowMs + effective;
    }

    // ---------------- helpers ----------------

    private static String readAll(InputStream in) throws IOException {
        if (in == null) return "";
        try (BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder(512);
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
            return sb.toString();
        }
    }

    private static String enc(String s) {
        try { return URLEncoder.encode(s, "UTF-8"); }
        catch (UnsupportedEncodingException e) { return s; }
    }

    private static String required(Properties p, String key) {
        String v = p.getProperty(key);
        if (v == null || v.trim().isEmpty())
            throw new IllegalArgumentException("Missing required property: " + key);
        return v.trim();
    }

    private static int parseInt(String v, int def) {
        if (v == null) return def;
        try { return Integer.parseInt(v.trim()); } catch (Exception ignore) { return def; }
    }

    private static String text(JsonNode n, String k) {
        JsonNode x = n.get(k);
        return (x == null || x.isNull()) ? null : x.asText();
    }

    private static int intVal(JsonNode n, String k, int def) {
        JsonNode x = n.get(k);
        return (x == null || x.isNull()) ? def : x.asInt(def);
    }
}
