package es.us.isa.httpmutator.experiment.rq3.evomaster.utils;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.atomic.AtomicInteger;

import io.restassured.filter.Filter;
import io.restassured.filter.FilterContext;
import io.restassured.response.Response;
import io.restassured.specification.FilterableRequestSpecification;
import io.restassured.specification.FilterableResponseSpecification;

/**
 * Experimental REST Assured {@link Filter} that dumps each
 * (request, response) pair to WebScarab-style plain-text files.
 *
 * For every interaction, two files are written:
 *   - <index>-req.txt
 *   - <index>-res.txt
 *
 * This filter is intended ONLY for experimental logging and should
 * not be considered part of the stable public API.
 */
public class WebScarabDumpFilter implements Filter {

    private static final AtomicInteger GLOBAL_INDEX = new AtomicInteger(0);

    private final Path outputDir;

    /**
     * Create a WebScarabDumpFilter with an explicit output directory.
     *
     * @param outputDir directory where dump files will be written
     */
    public WebScarabDumpFilter(Path outputDir) {
        this.outputDir = outputDir;
        try {
            Files.createDirectories(outputDir);
        } catch (IOException e) {
            throw new RuntimeException("Failed to create WebScarab dump directory: " + outputDir, e);
        }
    }

    /**
     * Create a WebScarabDumpFilter that writes files to:
     *   target/webscarab-dump
     */
    public WebScarabDumpFilter() {
        this(defaultOutputDir());
    }

    private static Path defaultOutputDir() {
        return Paths.get("target", "webscarab-dump");
    }

    @Override
    public Response filter(FilterableRequestSpecification requestSpec,
                           FilterableResponseSpecification responseSpec,
                           FilterContext ctx) {

        int index = GLOBAL_INDEX.getAndIncrement();
        String baseName = String.valueOf(index);

        // 1) request -> WebScarab txt
        String reqText = null;
        try {
            reqText = RestAssuredWebScarabConverter.toWebScarabRequest(requestSpec);
        } catch (Exception e) {
            throw new RuntimeException("[WebScarabDumpFilter] Failed to convert request to WebScarab format for "
                    + baseName + ": " + e.getMessage(), e);
        }

        // 2) execute request，and get the response
        Response response = ctx.next(requestSpec, responseSpec);

        // 3) response -> WebScarab txt
        String resText = null;
        try {
            resText = RestAssuredWebScarabConverter.toWebScarabResponse(response);
        } catch (Exception e) {
            throw new RuntimeException("[WebScarabDumpFilter] Failed to convert response to WebScarab format for "
                    + baseName + ": " + e.getMessage(), e);
        }

        // 4) write files for req/res
        try {
            Path reqFile = outputDir.resolve(baseName + "-req.txt");
            Files.write(reqFile, reqText.getBytes(StandardCharsets.UTF_8));

            Path resFile = outputDir.resolve(baseName + "-res.txt");
            Files.write(resFile, resText.getBytes(StandardCharsets.UTF_8));
        } catch (IOException ioe) {
            System.err.println("[WebScarabDumpFilter] Failed to write dump files for "
                    + baseName + " in directory " + outputDir + ": " + ioe.getMessage());
            ioe.printStackTrace(System.err);
        }

        // for industry apis
        try {
            Thread.sleep(1000);
        } catch (InterruptedException ignored) {
            Thread.currentThread().interrupt(); // Preserve interrupt status without throwing.
        }

        return response;
    }
}
