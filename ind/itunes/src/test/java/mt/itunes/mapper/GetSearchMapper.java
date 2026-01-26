package mt.itunes.mapper;

import es.us.isa.httpmutator.experiment.endpoint.test.model.LogRecord;
import es.us.isa.httpmutator.experiment.endpoint.test.util.CsvRowMapper;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class GetSearchMapper implements CsvRowMapper {
    public static final List<String> TERM_LIST = Arrays.asList(
            "Tom+Hanks",
            "Action",
            "Taylor+Swift",
            "Piper",
            "Kevin+Feige",
            "PG-13",
            "Christopher+Nolan",
            "2010",
            "Inception",
            "Marvel+Studios",
            "Interstellar",
            "1",
            "superhero",
            "Love+Story",
            "English",
            "JK+Rowling",
            "fitness",
            "Chillout+Mix",
            "Hans+Zimmer",
            "1989",
            "Hello",
            "Adobe",
            "Pilot",
            "Breaking+Bad",
            "Season+1",
            "Maroon+5",
            "Shape+of+You"
    );
    private static final Map<String, String> ATTRIBUTE_TERM_MAP = new HashMap<>();

    static {
        ATTRIBUTE_TERM_MAP.put("actorTerm", "Tom+Hanks");
        ATTRIBUTE_TERM_MAP.put("genreIndex", "Action");
        ATTRIBUTE_TERM_MAP.put("artistTerm", "Taylor+Swift");
        ATTRIBUTE_TERM_MAP.put("shortFilmTerm", "Piper");
        ATTRIBUTE_TERM_MAP.put("producerTerm", "Kevin+Feige");
        ATTRIBUTE_TERM_MAP.put("ratingTerm", "PG-13");
        ATTRIBUTE_TERM_MAP.put("directorTerm", "Christopher+Nolan");
        ATTRIBUTE_TERM_MAP.put("releaseYearTerm", "2010");
        ATTRIBUTE_TERM_MAP.put("featureFilmTerm", "Inception");
        ATTRIBUTE_TERM_MAP.put("movieArtistTerm", "Marvel+Studios");
        ATTRIBUTE_TERM_MAP.put("movieTerm", "Interstellar");
        ATTRIBUTE_TERM_MAP.put("ratingIndex", "1");
        ATTRIBUTE_TERM_MAP.put("descriptionTerm", "superhero");
        ATTRIBUTE_TERM_MAP.put("titleTerm", "Love+Story");
        ATTRIBUTE_TERM_MAP.put("languageTerm", "English");
        ATTRIBUTE_TERM_MAP.put("authorTerm", "JK+Rowling");
        ATTRIBUTE_TERM_MAP.put("keywordsTerm", "fitness");
        ATTRIBUTE_TERM_MAP.put("mixTerm", "Chillout+Mix");
        ATTRIBUTE_TERM_MAP.put("composerTerm", "Hans+Zimmer");
        ATTRIBUTE_TERM_MAP.put("albumTerm", "1989");
        ATTRIBUTE_TERM_MAP.put("songTerm", "Hello");
        ATTRIBUTE_TERM_MAP.put("softwareDeveloper", "Adobe");
        ATTRIBUTE_TERM_MAP.put("tvEpisodeTerm", "Pilot");
        ATTRIBUTE_TERM_MAP.put("showTerm", "Breaking+Bad");
        ATTRIBUTE_TERM_MAP.put("tvSeasonTerm", "Season+1");
        ATTRIBUTE_TERM_MAP.put("allArtistTerm", "Maroon+5");
        ATTRIBUTE_TERM_MAP.put("allTrackTerm", "Shape+of+You");
    }

    @Override
    public LogRecord map(String path, String httpMethod, Map<String, String> row) {
        Map<String, String> n = new HashMap<>();

        // parameters: term, country, media, entity, attribute, limit, lang, explicit
//        putIfPresent(row, n, "term");
        putIfPresent(row, n, "country");
        putIfPresent(row, n, "media");
        putIfPresent(row, n, "entity");
        putIfPresent(row, n, "attribute");
        putIfPresent(row, n, "limit");
        putIfPresent(row, n, "lang");
        putIfPresent(row, n, "explicit");

        Map<String, String> queryParams = new HashMap<>(n);
        if (!row.containsKey("term")) {
            String term = null;
            String attribute = n.get("attribute");
            if (attribute != null) {
                term = ATTRIBUTE_TERM_MAP.get(attribute);
            } else {
                // no attribute: use a random term from the list
                int idx = (int) (Math.random() * TERM_LIST.size());
                term = TERM_LIST.get(idx);
            }
            queryParams.put("term", term);
        } else {
            queryParams.put("term", row.get("term"));
        }
        return LogRecord.builder()
                .withPath(path)
                .withHttpMethod(httpMethod)
                .withQueryParameters(queryParams)
                .build();
    }
}
