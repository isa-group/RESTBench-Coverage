package es.us.isa.httpmutator.experiment.rq3.evomaster.utils;

import io.restassured.http.Header;
import io.restassured.http.Headers;
import io.restassured.response.Response;
import io.restassured.specification.FilterableRequestSpecification;

import java.net.URI;
import java.util.Locale;

/**
 * Utility class to convert RestAssured requests and responses
 * into WebScarab-style plain-text HTTP messages.
 *
 * This is intended for experimental use (e.g., logging traffic used
 * in mutation testing) and is NOT meant as part of the stable public API.
 */
public class RestAssuredWebScarabConverter {
    private static final String CRLF = "\r\n";

    private RestAssuredWebScarabConverter() {
        // utility class
    }

    /**
     * Convert a RestAssured {@link FilterableRequestSpecification} into a
     * WebScarab-style HTTP request message (request-xxx-req.txt).
     *
     * Format:
     *  GET /path?query HTTP/1.1
     *  Host: example.com[:port]
     *  Header1: value
     *  ...
     *
     *  <optional body>
     */
    public static String toWebScarabRequest(FilterableRequestSpecification req) {
        if (req == null) {
            throw new IllegalArgumentException("request specification cannot be null");
        }

        StringBuilder sb = new StringBuilder();

        // === Request line ===
        // e.g., GET /api/foo?bar=1 HTTP/1.1
        URI uri = URI.create(req.getURI());

        String method = req.getMethod() == null ? "GET" : req.getMethod();
        String path = uri.getRawPath();
        if (path == null || path.isEmpty()) {
            path = "/";
        }

        sb.append(method)
                .append(" ")
                .append(path);

        String query = uri.getRawQuery();
        if (query != null && !query.isEmpty()) {
            sb.append("?").append(query);
        }

        sb.append(" HTTP/1.1").append(CRLF);

        // === Host header ===
        Headers headers = req.getHeaders();
        boolean hasHostHeader = hasHostHeader(headers);

        if (!hasHostHeader) {
            String host = uri.getHost();
            if (host != null && !host.isEmpty()) {
                sb.append("Host: ").append(host);
                int port = uri.getPort();
                if (port != -1) {
                    sb.append(":").append(port);
                }
                sb.append(CRLF);
            }
        }

        // === Other headers ===
        if (headers != null) {
            for (Header h : headers) {
                if (!"host".equalsIgnoreCase(h.getName())) {
                    sb.append(h.getName())
                            .append(": ")
                            .append(h.getValue())
                            .append(CRLF);
                }
            }
        }

        sb.append(CRLF);

        // === Body ===
        Object body = req.getBody();
        if (body != null) {
            sb.append(body.toString());
        }

        return sb.toString();
    }

    /**
     * Convert a RestAssured {@link Response} into a WebScarab-style HTTP
     * response message (request-xxx-res.txt).
     *
     * Format:
     *  HTTP/1.1 200 OK
     *  Header1: value
     *  ...
     *
     *  <body>
     */
    public static String toWebScarabResponse(Response response) {
        if (response == null) {
            throw new IllegalArgumentException("response cannot be null");
        }

        StringBuilder sb = new StringBuilder();

        // === Status line ===
        String statusLine = response.getStatusLine();
        int statusCode = response.getStatusCode();

        if (statusLine != null && !statusLine.trim().isEmpty()) {
            sb.append(statusLine.trim()).append(CRLF);
        } else {
            sb.append("HTTP/1.1 ")
                    .append(statusCode)
                    .append(" ")
                    .append(getReasonPhrase(statusCode))
                    .append(CRLF);
        }

        // === Headers ===
        Headers headers = response.getHeaders();
        if (headers != null) {
            for (Header h : headers) {
                String name = h.getName();
                if (name.equals("content-type")) {
                    name = "Content-Type";
                }
                sb.append(name)
                        .append(": ")
                        .append(h.getValue())
                        .append(CRLF);
            }
        }

        sb.append(CRLF);

        // === Body ===
        String body = null;
        try {
            body = response.getBody().asString();
        } catch (Exception e) {
            // ignore, no body
        }

        if (body != null && !body.isEmpty()) {
            sb.append(body);
        }

        return sb.toString();
    }

    // ----------------------------------------------------
    // Helpers
    // ----------------------------------------------------

    private static boolean hasHostHeader(Headers headers) {
        if (headers == null) {
            return false;
        }
        for (Header h : headers) {
            if ("host".equalsIgnoreCase(h.getName())) {
                return true;
            }
        }
        return false;
    }

    private static String getReasonPhrase(int statusCode) {
        return switch (statusCode) {
            case 200 -> "OK";
            case 201 -> "Created";
            case 202 -> "Accepted";
            case 204 -> "No Content";
            case 301 -> "Moved Permanently";
            case 302 -> "Found";
            case 304 -> "Not Modified";
            case 400 -> "Bad Request";
            case 401 -> "Unauthorized";
            case 403 -> "Forbidden";
            case 404 -> "Not Found";
            case 405 -> "Method Not Allowed";
            case 409 -> "Conflict";
            case 422 -> "Unprocessable Entity";
            case 500 -> "Internal Server Error";
            case 502 -> "Bad Gateway";
            case 503 -> "Service Unavailable";
            default -> "Unknown";
        };
    }
}
