package com.securednodedynamics.downtify;

import android.media.MediaMetadataRetriever;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Genre labels for Android Auto, decoded from on-disk audio tags. */
final class AutoLibraryTags {

    private static final Pattern ID3_NUMBER = Pattern.compile(
        "^\\((\\d{1,3})\\)\\s*(.*)$"
    );
    private static final Pattern BARE_NUMBER = Pattern.compile("^\\d{1,3}$");

    // ID3v1 + Winamp extensions. Unknown indexes fall back to the raw tag text.
    static final String[] ID3_GENRES = {
        "Blues",
        "Classic Rock",
        "Country",
        "Dance",
        "Disco",
        "Funk",
        "Grunge",
        "Hip-Hop",
        "Jazz",
        "Metal",
        "New Age",
        "Oldies",
        "Other",
        "Pop",
        "R&B",
        "Rap",
        "Reggae",
        "Rock",
        "Techno",
        "Industrial",
        "Alternative",
        "Ska",
        "Death Metal",
        "Pranks",
        "Soundtrack",
        "Euro-Techno",
        "Ambient",
        "Trip-Hop",
        "Vocal",
        "Jazz+Funk",
        "Fusion",
        "Trance",
        "Classical",
        "Instrumental",
        "Acid",
        "House",
        "Game",
        "Sound Clip",
        "Gospel",
        "Noise",
        "Alt Rock",
        "Bass",
        "Soul",
        "Punk",
        "Space",
        "Meditative",
        "Instrumental Pop",
        "Instrumental Rock",
        "Ethnic",
        "Gothic",
        "Darkwave",
        "Techno-Industrial",
        "Electronic",
        "Pop-Folk",
        "Eurodance",
        "Dream",
        "Southern Rock",
        "Comedy",
        "Cult",
        "Gangsta",
        "Top 40",
        "Christian Rap",
        "Pop/Funk",
        "Jungle",
        "Native American",
        "Cabaret",
        "New Wave",
        "Psychedelic",
        "Rave",
        "Showtunes",
        "Trailer",
        "Lo-Fi",
        "Tribal",
        "Acid Punk",
        "Acid Jazz",
        "Polka",
        "Retro",
        "Musical",
        "Rock & Roll",
        "Hard Rock",
        "Folk",
        "Folk/Rock",
        "National Folk",
        "Swing",
        "Fast Fusion",
        "Bebob",
        "Latin",
        "Revival",
        "Celtic",
        "Bluegrass",
        "Avantgarde",
        "Gothic Rock",
        "Progressive Rock",
        "Psychedelic Rock",
        "Symphonic Rock",
        "Slow Rock",
        "Big Band",
        "Chorus",
        "Easy Listening",
        "Acoustic",
        "Humour",
        "Speech",
        "Chanson",
        "Opera",
        "Chamber Music",
        "Sonata",
        "Symphony",
        "Booty Bass",
        "Primus",
        "Porn Groove",
        "Satire",
        "Slow Jam",
        "Club",
        "Tango",
        "Samba",
        "Folklore",
        "Ballad",
        "Power Ballad",
        "Rhythmic Soul",
        "Freestyle",
        "Duet",
        "Punk Rock",
        "Drum Solo",
        "A cappella",
        "Euro-House",
        "Dance Hall",
        "Goa",
        "Drum & Bass",
        "Club-House",
        "Hardcore",
        "Terror",
        "Indie",
        "BritPop",
        "Negerpunk",
        "Polsk Punk",
        "Beat",
        "Christian Gangsta Rap",
        "Heavy Metal",
        "Black Metal",
        "Crossover",
        "Contemporary Christian",
        "Christian Rock",
        "Merengue",
        "Salsa",
        "Thrash Metal",
        "Anime",
        "JPop",
        "Synthpop",
    };

    private AutoLibraryTags() {}

    static String readGenre(File file) {
        MediaMetadataRetriever retriever = new MediaMetadataRetriever();
        try {
            retriever.setDataSource(file.getAbsolutePath());
            return decodeGenre(
                retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_GENRE)
            );
        } catch (Exception ignored) {
            return "";
        } finally {
            try {
                retriever.release();
            } catch (Exception ignored) {
                // Ignore close failures after a successful or failed read.
            }
        }
    }

    static String decodeGenre(String raw) {
        String value = raw == null ? "" : raw.trim();
        if (value.isEmpty()) return "";

        Matcher wrapped = ID3_NUMBER.matcher(value);
        if (wrapped.matches()) {
            String named = wrapped.group(2) == null ? "" : wrapped.group(2).trim();
            if (!named.isEmpty()) return named;
            return genreFromIndex(wrapped.group(1));
        }
        if (BARE_NUMBER.matcher(value).matches()) {
            return genreFromIndex(value);
        }
        return value;
    }

    static List<String> splitGenres(String genre) {
        List<String> names = new ArrayList<>();
        String value = genre == null ? "" : genre.trim();
        if (value.isEmpty()) return names;
        for (String part : value.split("\\s*[;,]\\s*")) {
            String name = part.trim();
            if (!name.isEmpty() && !names.contains(name)) names.add(name);
        }
        if (names.isEmpty()) names.add(value);
        return names;
    }

    private static String genreFromIndex(String indexText) {
        try {
            int index = Integer.parseInt(indexText);
            if (index >= 0 && index < ID3_GENRES.length) {
                return ID3_GENRES[index];
            }
        } catch (NumberFormatException ignored) {
            // Fall through to the raw numeric label.
        }
        return indexText;
    }

    static String displayGenre(String tagged) {
        String decoded = decodeGenre(tagged);
        return decoded.isEmpty() ? "Unknown genre" : decoded;
    }
}
