package org.zalando.catwatch.backend.repo.util;

import java.util.Calendar;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.zalando.catwatch.backend.repo.ContributorRepository;
import org.zalando.catwatch.backend.repo.ProjectRepository;
import org.zalando.catwatch.backend.repo.StatisticsRepository;
import org.zalando.catwatch.backend.repo.builder.ContributorBuilder;
import org.zalando.catwatch.backend.repo.builder.ProjectBuilder;
import org.zalando.catwatch.backend.repo.builder.StatisticsBuilder;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.TimeZone;

import static org.zalando.catwatch.backend.repo.util.DatabasePing.isDatabaseAvailable;

@Component
public class DatabasePopulator {

    private final StatisticsRepository statisticsRepository;
    private final ProjectRepository projectRepository;
    private final ContributorRepository contributorRepository;
    private final JdbcTemplate jdbcTemplate;

    // ======= Fixed random source and helper methods (scoped to this class only) =======
    private static final long FIXED_SEED = 20250101L;
    private static long ID_SEQ = 1000L;

    private static final String[] LANGS = {
            "Java", "JS", "HTML5", "CSS", "Python", "C++",
            "Go", "Scala", "Groovy", "C#", "Clojure", "VB", "ObjectiveC"
    };

    // Generate sequential IDs (instead of random UUIDs)
    private static long nextId() { return ID_SEQ++; }

    // Deterministic project name generator
    private static String projectName(int i) {
        return String.format("galanto-project-%02d", i);
    }

    private static int forksFor(int projectIndex, int snapshotIndex) {
        return 1 + (projectIndex + snapshotIndex) % 4;        // range [1, 4]
    }

    private static int starsFor(int projectIndex, int snapshotIndex) {
        return 1 + (projectIndex * 3 + snapshotIndex * 2) % 10; // range [1, 10]
    }

    private static int commitsFor(int projectIndex, int snapshotIndex) {
        return 1 + (projectIndex * 17 + snapshotIndex * 7) % 1000; // range [1, 1000]
    }

    private static int contributorsFor(int projectIndex, int snapshotIndex) {
        return 1 + (projectIndex * 11 + snapshotIndex * 5) % 1000; // range [1, 1000]
    }

    private static int scoreFor(int projectIndex, int snapshotIndex) {
        return 1 + (projectIndex * 23 + snapshotIndex * 13) % 100; // range [1, 100]
    }

    // Deterministic language assignment
    private static String language(int i) {
        return LANGS[i % LANGS.length];
    }

    /**
     * Deterministic snapshot date generation.
     * Produces a stable timeline starting at 2024-01-01 UTC,
     * adding `index` days.
     */
    private static Date snapshotDateForIndex(int index) {
        Calendar cal = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
        cal.clear();
        cal.set(2024, Calendar.JANUARY, 1, 0, 0, 0);
        cal.add(Calendar.DAY_OF_YEAR, index);
        return cal.getTime();
    }
    // ================================================================================

    @Autowired
    public DatabasePopulator(StatisticsRepository statisticsRepository,
                             ProjectRepository projectRepository,
                             ContributorRepository contributorRepository,
                             JdbcTemplate jdbcTemplate) {
        this.statisticsRepository = statisticsRepository;
        this.projectRepository = projectRepository;
        this.contributorRepository = contributorRepository;
        this.jdbcTemplate = jdbcTemplate;
    }

    public void populateTestData() {

        if (!isDatabaseAvailable(jdbcTemplate)) {
            return;                             // return so that the application context can start at least
        }

        // create statistics for two companies (latest)
        new StatisticsBuilder(statisticsRepository) //
            .organizationName("galanto") //
            .publicProjectCount(34) //
            .allStarsCount(54) //
            .allForksCount(110) //
            .days(1)
            .save();

        new StatisticsBuilder(statisticsRepository) //
            .organizationName("galanto-italic") //
            .publicProjectCount(56) //
            .allStarsCount(93) //
            .allForksCount(249) //
            .days(1)
            .save();

        // create projects for galanto
        List<Date> snapshots = new ArrayList<>();
        for (int si = 0; si < 100; si++) {
            snapshots.add(snapshotDateForIndex(si));
        }

        for (int projectIndex = 0; projectIndex < 10; projectIndex++) {
            Long gitHubProjectId = nextId();
            String name = projectName(projectIndex);
            String language = language(projectIndex);

            for (int snapshotIndex = 0; snapshotIndex < snapshots.size(); snapshotIndex++) {
                Date snapshot = snapshots.get(snapshotIndex);

                new ProjectBuilder(projectRepository)
                    .organizationName("galanto")
                    .name(name)
                    .gitHubProjectId(gitHubProjectId)
                    .primaryLanguage(language)
                    .snapshotDate(snapshot)
                    .forksCount(forksFor(projectIndex, snapshotIndex))
                    .starsCount(starsFor(projectIndex, snapshotIndex))
                    .commitsCount(commitsFor(projectIndex, snapshotIndex))
                    .contributorsCount(contributorsFor(projectIndex, snapshotIndex))
                    .score(scoreFor(projectIndex, snapshotIndex))
                    .save();
            }
        }

        // create contributors for galanto
        for (int i = 0; i < 2; i++) {
            new ContributorBuilder(contributorRepository)
                .organizationName("galanto")
                .save();
        }
    }
}
