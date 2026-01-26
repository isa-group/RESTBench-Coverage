package mt.se.devscout.scoutapi;

import java.io.*;
import java.net.URL;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.Statement;
import java.util.UUID;
import java.util.stream.Collectors;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;
import se.devscout.scoutapi.ScoutAPIApplication;
import se.devscout.scoutapi.ScoutAPIConfiguration;

public class ScoutAPISutManager implements SutManager {
    private static final org.slf4j.Logger logger = org.slf4j.LoggerFactory.getLogger(ScoutAPISutManager.class);

    // Absolute path to the Dropwizard YAML configuration on the classpath
    private static final String CONFIG_YML_PATH;
    // Absolute path to the database initialization SQL on the classpath
    private static final String INIT_DB_SCRIPT_PATH;

    static {
        ClassLoader cl = ScoutAPISutManager.class.getClassLoader();
        URL ymlUrl = cl.getResource("scout-api.yml");
        URL sqlUrl = cl.getResource("init_db.sql");
        if (ymlUrl == null) {
            throw new IllegalStateException(
                    "scout_api.yml not found. Please put it under src/main/resources");
        }
        if (sqlUrl == null) {
            throw new IllegalStateException(
                    "init_db.sql not found. Please put it under src/main/resources");
        }
        CONFIG_YML_PATH = ymlUrl.getPath();
        INIT_DB_SCRIPT_PATH = sqlUrl.getPath();
    }

    public static final class CleanupHandles {
        public final Path baseRunDir;       // root dir for this run (contains config/, temp/, media-files/)
        public final Path tempFolder;       // per-run temp folder
        public final Path mediaFilesFolder; // per-run media folder
        public final Path perRunYaml;       // the generated YAML used to start DW
        public final String h2Url;          // datasource URL
        public CleanupHandles(Path baseRunDir, Path tempFolder, Path mediaFilesFolder,
                              Path perRunYaml, String h2Url) {
            this.baseRunDir = baseRunDir;
            this.tempFolder = tempFolder;
            this.mediaFilesFolder = mediaFilesFolder;
            this.perRunYaml = perRunYaml;
            this.h2Url = h2Url;
        }
    }

    private static void createDirectoriesQuietly(Path p) {
        try {
            Files.createDirectories(p);
            // Mark for deletion on JVM exit as a fallback (best-effort)
            p.toFile().deleteOnExit();
        } catch (IOException e) {
            // Not fatal; log and continue
            logger.warn("Failed to create directories for {}: {}", p, e.toString());
        }
    }


    /**
     * Starts the ScoutAPI application on a random available port,
     * and executes the SQL init script to set up the in-memory H2 database.
     */
    @Override
    public SutContext start() {
        final String runId = "sut-" + UUID.randomUUID();
        final Path baseRunDir = Paths.get("./target/temp").resolve(runId);
        final Path tempFolder = baseRunDir.resolve("temp");
        final Path mediaFolder = baseRunDir.resolve("media-files");
        final Path configDir = baseRunDir.resolve("config");

        createDirectoriesQuietly(tempFolder);
        createDirectoriesQuietly(configDir);

        // generate specific config file
        ObjectMapper yaml = new ObjectMapper(new YAMLFactory());
        final JsonNode root;
        try (InputStream in = Files.newInputStream(Paths.get(CONFIG_YML_PATH))) {
            root = yaml.readTree(in);
        } catch (Exception e) {
            throw new RuntimeException("Failed to read ScoutAPI configuration", e);
        }
        logger.debug("Original config: {}", root.toString());
        ObjectNode obj = (ObjectNode) root;
        obj.put("tempFolder", tempFolder.toString());
        obj.put("mediaFilesFolder", mediaFolder.toString());


        Path perRunYaml = configDir.resolve("scout-api-" + runId + ".yml");
        try {
            yaml.writeValue(perRunYaml.toFile(), obj);
        } catch (Exception e) {
            throw new RuntimeException("Failed to write per-run ScoutAPI configuration", e);
        }

        // Bind Dropwizard to a random port
        System.setProperty("dw.server.connector.port", "0");

        // Start HTTP server
        ScoutAPIApplication app = new ScoutAPIApplication();
        try {
            app.run("server", perRunYaml.toString());
            logger.info("ScoutAPIApplication started with config: " + perRunYaml.toString());
        } catch (Exception e) {
            throw new RuntimeException("Failed to start ScoutAPIApplication", e);
        }

        // Wait for Jetty to start
        try {
            Thread.sleep(3000);
            while (!app.getJettyServer().isStarted()) {
                Thread.sleep(500);
            }
        } catch (InterruptedException ignored) {
        }
        logger.info("Jetty server started on port: " + app.getJettyPort());
        // Execute SQL init script on H2
        // The try-with-resources ensures that both the Connection and the
        // BufferedReader (and its underlying FileInputStream) are automatically closed
        // try (Connection conn = app.getConnection();
        //         BufferedReader reader = new BufferedReader(
        //                 new InputStreamReader(new FileInputStream(INIT_DB_SCRIPT_PATH)))) {

        //     String sql = reader.lines().collect(Collectors.joining("\n"));
        //     for (String stmt : sql.split(";")) {
        //         if (!stmt.trim().isEmpty()) {
        //             try (Statement s = conn.createStatement()) {
        //                 s.execute(stmt);
        //             }
        //         }
        //     }
        //     logger.info("Executed SQL init script: " + INIT_DB_SCRIPT_PATH);
        // } catch (Exception e) {
        //     throw new RuntimeException("Failed to execute SQL init script", e);
        // }

        String h2Url = obj.path("database").path("url").asText(null);
        CleanupHandles handles = new CleanupHandles(baseRunDir, tempFolder, mediaFolder, perRunYaml, h2Url);

        // Build SutContext with the running application
        int port = app.getJettyPort();
        String baseUri = "http://localhost:" + port;
        return new SutContext.Builder()
                .port(port)
                .baseUri(baseUri)
                .register(ScoutAPIApplication.class, app)
                .register(CleanupHandles.class, handles)
                .build();
    }


    private static void deleteRecursivelyQuietly(Path root, String label) {
        if (root == null) return;
        try {
            if (!Files.exists(root)) {
                logger.info("{} does not exist, skip: {}", label, root);
                return;
            }
            Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    Files.deleteIfExists(file);
                    return FileVisitResult.CONTINUE;
                }
                public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                    Files.deleteIfExists(dir);
                    return FileVisitResult.CONTINUE;
                }
            });
            logger.info("Deleted {} recursively: {}", label, root);
        } catch (Exception e) {
            logger.warn("Failed to delete {} at {}: {}", label, root, e.toString());
        }
    }


    /**
     * Stops the ScoutAPI application using the instance from SutContext.
     */
    @Override
    public void stop(SutContext ctx) {
        ScoutAPIApplication app = ctx.getService(ScoutAPIApplication.class);
            CleanupHandles handles = ctx.getService(CleanupHandles.class);
        if (app != null && app.getJettyServer() != null) {
            try {
                app.getJettyServer().stop();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        if (handles != null  && handles.h2Url != null) {
            try (Connection c = DriverManager.getConnection(handles.h2Url, "sa", "");
                 Statement st = c.createStatement()) {
                st.execute("SHUTDOWN");
                logger.info("H2 SHUTDOWN executed for URL: {}", handles.h2Url);
            } catch (Exception e) {
                logger.warn("H2 SHUTDOWN skipped/failed for {}: {}", handles.h2Url, e.toString());
            }
        }
        if (handles != null && handles.baseRunDir != null) {
            deleteRecursivelyQuietly(handles.baseRunDir, "baseRunDir");
        } else {
            logger.warn("No CleanupHandles present; nothing to delete.");
        }
    }
}
