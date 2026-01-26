package mt.com.giassi.microservice.demo2;

import java.lang.management.ManagementFactory;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.Duration;
import java.util.Map;
import java.util.Objects;
import java.util.Properties;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.testcontainers.containers.MySQLContainer;

import com.giassi.microservice.demo2.Microservice2Application;

import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutContext;
import es.us.isa.httpmutator.experiment.endpoint.test.sut.SutManager;

public class UserManagementSutManager implements SutManager {
    private static final Logger logger = LoggerFactory.getLogger(UserManagementSutManager.class);

    // ── External MySQL config (Docker Compose service name) ──────────
    private static final String MYSQL_HOST = "URM-MYSQL"; // Compose service name
    private static final int MYSQL_PORT = 3306;
    private static final String MYSQL_USER = "root";
    private static final String MYSQL_PASS = "root";
    private static final String MYSQL_BASE_DB = "mysql"; // connect to 'mysql' db to create/drop schemas

    // JDBC params for MySQL 8
    private static final String JDBC_COMMON_PARAMS =
            "useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&rewriteBatchedStatements=true";


    @Override
    public SutContext start() {
        // 1) Build a unique schema name: users_mt_<pid>_<nano36>
        final String jvmName = ManagementFactory.getRuntimeMXBean().getName(); // like "12345@hostname"
        final String pid = jvmName.contains("@") ? jvmName.substring(0, jvmName.indexOf('@')) : jvmName;
        final String schema = "users_mt_" + pid + "_" + Long.toString(System.nanoTime(), 36);

        // 2) Ensure MySQL is reachable and create the schema
        final String adminUrl = String.format("jdbc:mysql://%s:%d/%s?%s", MYSQL_HOST, MYSQL_PORT, MYSQL_BASE_DB, JDBC_COMMON_PARAMS);
        waitForMysql(adminUrl, MYSQL_USER, MYSQL_PASS, Duration.ofSeconds(60));
        createSchema(adminUrl, MYSQL_USER, MYSQL_PASS, schema);

        // 3) Start Spring Boot app on a random port with this schema
        final String appJdbcUrl = String.format("jdbc:mysql://%s:%d/%s?%s",
                MYSQL_HOST, MYSQL_PORT, schema, JDBC_COMMON_PARAMS);

        SpringApplication app = new SpringApplication(Microservice2Application.class);
        ConfigurableApplicationContext ctx = app.run(new String[]{
                "--server.port=0",
                "--spring.datasource.url=" + appJdbcUrl,
                "--spring.datasource.username=" + MYSQL_USER,
                "--spring.datasource.password=" + MYSQL_PASS,
                "--spring.jpa.hibernate.ddl-auto=none",
                "--spring.datasource.initialization-mode=always"
        });

        Integer port = (Integer) ((Map<?, ?>) Objects.requireNonNull(ctx.getEnvironment()
                        .getPropertySources()
                        .get("server.ports"))
                .getSource())
                .get("local.server.port");

        String baseUri = String.format("http://localhost:%d", port);
        logger.info("[UserManagement] started at {}", baseUri);

        // 4) Build and return the SutContext for test framework consumption
        return new SutContext.Builder()
                .baseUri(baseUri)
                .port(port)
                .register(String.class, schema)
                .register(ConfigurableApplicationContext.class, ctx)
                .build();
    }

    @Override
    public void stop(SutContext sutContext) {
        ConfigurableApplicationContext ctx = sutContext.getService(ConfigurableApplicationContext.class);
        String schema = sutContext.getService(String.class);

        if (ctx != null) {
            ctx.close();
            logger.info("[UserManagement] Spring context closed");
        }
        // Drop schema to keep MySQL clean (best-effort)
        if (schema != null && !schema.isEmpty()) {
            final String adminUrl = String.format("jdbc:mysql://%s:%d/%s?%s", MYSQL_HOST, MYSQL_PORT, MYSQL_BASE_DB, JDBC_COMMON_PARAMS);
            try {
                dropSchema(adminUrl, MYSQL_USER, MYSQL_PASS, schema);
                logger.info("[UserManagement] Dropped schema `{}`", schema);
            } catch (Exception e) {
                logger.warn("[UserManagement] Failed to drop schema `{}` (will ignore): {}", schema, e.toString());
            }
        }
    }

    // ────────────────────────── Helpers ──────────────────────────

    private static void waitForMysql(String jdbcUrl, String user, String pass, Duration timeout) {
        long deadline = System.nanoTime() + timeout.toNanos();
        SQLException last = null;

        while (System.nanoTime() < deadline) {
            try (Connection ignored = DriverManager.getConnection(jdbcUrl, user, pass)) {
                logger.info("[UserManagement] MySQL is reachable at {}", jdbcUrl);
                return;
            } catch (SQLException e) {
                last = e;
                try {
                    Thread.sleep(500);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                }
            }
        }
        throw new IllegalStateException("Timed out waiting for MySQL at " + jdbcUrl, last);
    }

    private static void createSchema(String adminUrl, String user, String pass, String schema) {
        String sql = "CREATE DATABASE IF NOT EXISTS `" + schema + "` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci";
        execDDL(adminUrl, user, pass, sql);
    }

    private static void dropSchema(String adminUrl, String user, String pass, String schema) {
        String sql = "DROP DATABASE IF EXISTS `" + schema + "`";
        execDDL(adminUrl, user, pass, sql);
    }

    private static void execDDL(String jdbcUrl, String user, String pass, String sql) {
        Properties props = new Properties();
        props.setProperty("user", user);
        props.setProperty("password", pass);
        try (Connection c = DriverManager.getConnection(jdbcUrl, props);
             Statement st = c.createStatement()) {
            st.execute(sql);
        } catch (SQLException e) {
            throw new IllegalStateException("DDL failed: " + sql + " on " + jdbcUrl, e);
        }
    }
}
