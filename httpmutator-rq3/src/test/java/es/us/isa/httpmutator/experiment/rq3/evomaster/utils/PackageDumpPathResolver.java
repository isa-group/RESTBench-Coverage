package es.us.isa.httpmutator.experiment.rq3.evomaster.utils;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Resolves dump directory paths based on a Java package name.
 *
 * Package naming convention:
 *
 *   ... . <configName> . <apiName> . <opName> . ...
 *
 * Example:
 *   package es.us.isa.httpmutator.experiment.rq3.evomaster.withBasicAssertions.Catwatch.getProjects.adv.assertall.eval10000.security.schema;
 *
 * Parsed:
 *   configName = withBasicAssertions
 *   apiName    = Catwatch
 *   opName     = getProjects
 *
 * Final directory structure:
 *
 *   baseDir/
 *     Catwatch-getProjects/
 *        withBasicAssertions/
 */
public final class PackageDumpPathResolver {

    private PackageDumpPathResolver() {}

    /**
     * Resolve the dump directories based on a package name.
     *
     * @param baseDir     the root output directory
     * @param packageName the Java package containing configName/apiName/opName
     */
    public static Path resolve(Path baseDir, String packageName) {
        if (packageName == null || packageName.trim().isEmpty()) {
            throw new IllegalArgumentException("packageName cannot be empty");
        }

        String[] parts = packageName.split("\\.");

        if (parts.length < 3) {
            throw new IllegalArgumentException("Package too short to extract config/api/op: " + packageName);
        }

        // ... <config>.<api>.<op> ...
        String configName = parts[parts.length - 8];
        String apiName    = parts[parts.length - 7];
        String opName     = parts[parts.length - 6];

        // API-op = Catwatch-getProjects
        String apiOpFolder = apiName + "-" + opName;

        Path apiOpDir = baseDir.resolve(apiOpFolder);
        Path configDir = apiOpDir.resolve(configName);

        try {
            Files.createDirectories(configDir);
        } catch (Exception e) {
            throw new RuntimeException("Failed to create dump directories: " + configDir, e);
        }

        return configDir;
    }

   public static void main(String[] args) {
        Path configPath = resolve(Paths.get("src/test/resources"), "package es.us.isa.httpmutator.experiment.rq3.evomaster.withBasicAssertions.Catwatch.getProjects.adv.assertall.eval10000.security.schema");
        System.out.println(configPath);
   }
}