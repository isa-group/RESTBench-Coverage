package es.us.isa.httpmutator.experiment.rq3.schemathesis;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import es.us.isa.httpmutator.core.HttpMutator;
import es.us.isa.httpmutator.core.reader.JsonlExchangeReader;
import es.us.isa.httpmutator.core.strategy.MutationStrategy;
import es.us.isa.httpmutator.core.strategy.RandomSingleStrategy;
import es.us.isa.httpmutator.core.writer.JsonlMutantWriter;
import es.us.isa.httpmutator.core.writer.ShardedZstdJsonlMutantWriter;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.OutputStreamWriter;
import java.nio.charset.CharsetEncoder;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.Objects;

public class SchemathesisMutantGenerator {
    private static final ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);

    private static final Path root = Paths.get("/app/expScripts/schemathesis-unique-reports");


    public static void main(String[] args) throws Exception {

        System.out.println("Root directory = " + root);

        if (!Files.isDirectory(root)) {
            System.err.println("Given root is not a directory: " + root);
            return;
        }

        // Iterate over the root directory:
        //    Each subdirectory represents an API name (e.g., Catwatch, GenomeNexus)
        try (DirectoryStream<Path> apiDirs = Files.newDirectoryStream(root, Files::isDirectory)) {
            for (Path apiDir : apiDirs) {
                String apiName = apiDir.getFileName().toString();
                System.out.println("== API: " + apiName + " ==");

                if (!apiName.equals("Deutschebahn")) {
                    continue;
                }

                // 3. Iterate over each operation inside the API directory
                try (DirectoryStream<Path> opDirs = Files.newDirectoryStream(apiDir, Files::isDirectory)) {
                    for (Path opDir : opDirs) {
                        String opName = opDir.getFileName().toString();
                        System.out.println("  -> Operation: " + opName);

                        // 4. Check if the directory contains httpmutator-input.jsonl
                        Path inputJsonl = opDir.resolve("httpmutator-inputs.jsonl");
                        if (Files.exists(inputJsonl) && Files.isRegularFile(inputJsonl)) {
                            System.out.println("     Found httpmutator-input.jsonl: " + inputJsonl);

                            Path mutantJsonl = opDir.resolve("mutants.jsonl");
                            if (Files.exists(mutantJsonl) && Files.isRegularFile(mutantJsonl)) {
                                System.out.println("    mutants.jsonl has already existed, skipped");
                                continue;
                            }

                            // 5. Perform mutation using HttpMutator
                            try {
                                mutateOneOperation(apiName, opName, inputJsonl);
                            } catch (Exception e) {
                                System.err.println("     [ERROR] Failed to mutate " + inputJsonl);
                                e.printStackTrace();
                            }
                        } else {
                            System.out.println("     (httpmutator-input.jsonl not found, skipping)");
                        }
                    }
                }
            }
        }
    }

    /**
     * Perform mutation on a single API operation.
     *
     * <p>Behavior depends on the API name:</p>
     * <ul>
     *   <li>For Deutschebahn and FDIC:
     *       <ul>
     *         <li>Use sharded Zstandard-compressed JSONL output</li>
     *         <li>Write results into {@code opDir/shared/*.jsonl.zst}</li>
     *       </ul>
     *   </li>
     *   <li>For all other APIs:
     *       <ul>
     *         <li>Preserve the original behavior</li>
     *         <li>Write a single {@code mutants.jsonl} file in the operation directory</li>
     *       </ul>
     *   </li>
     * </ul>
     */
    private static void mutateOneOperation(String apiName, String opName, Path inputJsonl) throws Exception {
        Objects.requireNonNull(inputJsonl, "inputJsonl must not be null");

        // Resolve the operation directory
        Path opDir = inputJsonl.getParent();
        if (opDir == null) {
            throw new IllegalStateException("inputJsonl has no parent directory: " + inputJsonl);
        }

        // Decide whether to use sharded + compressed output
        boolean useShared =
                apiName.equals("Deutschebahn") || apiName.equals("FDIC");

        System.out.println("     Mutating [" + apiName + "/" + opName + "]");
        System.out.println("     Input : " + inputJsonl);
        System.out.println("     Mode  : " + (useShared ? "SHARDED-ZSTD" : "JSONL"));

        // Mutation strategy (unchanged)
        MutationStrategy strategy = new RandomSingleStrategy();

        // Ensure the operation directory exists
        Files.createDirectories(opDir);

        // Reader for input exchanges
        JsonlExchangeReader reader = new JsonlExchangeReader();

        // UTF-8 encoder with replacement for malformed characters
        // This avoids crashes caused by invalid byte sequences
        CharsetEncoder safeEncoder = StandardCharsets.UTF_8
                .newEncoder()
                .onMalformedInput(CodingErrorAction.REPLACE)
                .onUnmappableCharacter(CodingErrorAction.REPLACE);

        if (!useShared) {
            /* =========================================================
             * Original behavior:
             *   - Write all mutants into a single mutants.jsonl file
             *   - No compression, no sharding
             * ========================================================= */

            Path outputJsonl = opDir.resolve("mutants.jsonl");
            System.out.println("     Output: " + outputJsonl);

            try (BufferedReader in = Files.newBufferedReader(inputJsonl, StandardCharsets.UTF_8);
                 BufferedWriter writer = new BufferedWriter(
                         new OutputStreamWriter(
                                 Files.newOutputStream(
                                         outputJsonl,
                                         StandardOpenOption.CREATE,
                                         StandardOpenOption.TRUNCATE_EXISTING
                                 ),
                                 safeEncoder
                         ));
                 HttpMutator httpMutator = new HttpMutator(42L)
                         .withMutationStrategy(strategy)
                         .addWriter(new JsonlMutantWriter(writer, true))
            ) {
                // Read each HTTP exchange and generate mutants
                reader.read(in, httpExchange -> {
                    try {
                        httpMutator.mutate(
                                httpExchange.getResponse(),
                                httpExchange.getId(),
                                m -> {
                                }
                        );
                    } catch (Exception e) {
                        throw new RuntimeException("Error mutating exchange", e);
                    }
                });
            }

        } else {
            /* =========================================================
             * Shared / sharded behavior (Deutschebahn, FDIC only):
             *   - Write compressed JSONL shards (*.jsonl.zst)
             *   - Each shard is written in a streaming fashion
             *   - Output directory: opDir/shared/
             * ========================================================= */

            Path sharedDir = opDir.resolve("shared");
            assertEmptyOrCreateDir(sharedDir, "sharedDir");

            System.out.println("     Output dir: " + sharedDir);

            // Mutable counter for mutants (used inside lambda)
            final long[] mutantCount = new long[] {0};

            try (BufferedReader in = Files.newBufferedReader(inputJsonl, StandardCharsets.UTF_8);
                 ShardedZstdJsonlMutantWriter writer =
                         new ShardedZstdJsonlMutantWriter(
                                 sharedDir,
                                 "mutants"   // shard filename prefix
                         );
                 HttpMutator httpMutator = new HttpMutator(42L)
                         .withMutationStrategy(strategy)
                         .addWriter(writer)
            ) {
                // Read each HTTP exchange and generate mutants
                reader.read(in, httpExchange -> {
                    try {
                        httpMutator.mutate(
                                httpExchange.getResponse(),
                                httpExchange.getId(),
                                m -> mutantCount[0]++
                        );
                    } catch (Exception e) {
                        throw new RuntimeException("Error mutating exchange", e);
                    }
                });
            }

            // Write mutant count after all shards are successfully written
            Path countFile = sharedDir.resolve("mutants-count.txt");
            Files.writeString(
                    countFile,
                    Long.toString(mutantCount[0]),
                    StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE,
                    StandardOpenOption.TRUNCATE_EXISTING
            );

            System.out.println("     Total mutants generated: " + mutantCount[0]);
        }
    }

    private static void assertEmptyOrCreateDir(Path dir, String label) throws Exception {
        Objects.requireNonNull(dir, "dir must not be null");

        if (Files.notExists(dir)) {
            Files.createDirectories(dir);
            return;
        }
        if (!Files.isDirectory(dir)) {
            throw new IllegalStateException(label + " exists but is not a directory: " + dir);
        }

        try (DirectoryStream<Path> ds = Files.newDirectoryStream(dir)) {
            for (Path p : ds) {
                throw new IllegalStateException(
                        label + " must be empty before writing shards, but found: " + p.getFileName()
                                + " in " + dir
                );
            }
        }
    }

}
