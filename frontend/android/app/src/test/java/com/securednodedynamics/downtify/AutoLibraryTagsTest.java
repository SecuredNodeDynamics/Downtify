package com.securednodedynamics.downtify;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.util.List;
import org.junit.Test;

public class AutoLibraryTagsTest {

    @Test
    public void decodesId3NumericGenres() {
        assertEquals("Hip-Hop", AutoLibraryTags.decodeGenre("(7)"));
        assertEquals("Pop", AutoLibraryTags.decodeGenre("(13)Pop"));
        assertEquals("Rock", AutoLibraryTags.decodeGenre("17"));
        assertEquals("R&B", AutoLibraryTags.decodeGenre("(14)"));
    }

    @Test
    public void keepsNamedGenreTags() {
        assertEquals("Indie Pop", AutoLibraryTags.decodeGenre("Indie Pop"));
        assertEquals("", AutoLibraryTags.decodeGenre("  "));
        assertEquals("Unknown genre", AutoLibraryTags.displayGenre(""));
        assertEquals("Jazz", AutoLibraryTags.displayGenre("Jazz"));
    }

    @Test
    public void splitsMultiGenreTags() {
        List<String> names = AutoLibraryTags.splitGenres("Hip-Hop; Rap");
        assertEquals(2, names.size());
        assertTrue(names.contains("Hip-Hop"));
        assertTrue(names.contains("Rap"));
    }
}
