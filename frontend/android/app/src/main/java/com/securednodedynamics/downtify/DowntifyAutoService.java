package com.securednodedynamics.downtify;

import android.content.Intent;
import android.media.MediaMetadataRetriever;
import android.net.Uri;
import android.os.Bundle;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.media3.common.C;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.session.LibraryResult;
import androidx.media3.session.MediaLibraryService;
import androidx.media3.session.MediaSession;
import com.google.common.collect.ImmutableList;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import java.io.File;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Native Android Auto / Automotive media surface for downloaded Downtify tracks.
 *
 * Android Auto renders its own UI from this browsable media tree, so this
 * service intentionally avoids phone-only Downtify actions like downloading.
 */
public class DowntifyAutoService extends MediaLibraryService {

    private static final String ROOT_ID = "downtify:auto:root";
    private static final String ARTISTS_ID = "downtify:auto:artists";
    private static final String ALBUMS_ID = "downtify:auto:albums";
    private static final String TRACKS_ID = "downtify:auto:tracks";
    private static final String ARTIST_PREFIX = "downtify:auto:artist:";
    private static final String ALBUM_PREFIX = "downtify:auto:album:";
    private static final String TRACK_PREFIX = "downtify:auto:track:";
    private static final long LIBRARY_CACHE_MS = 5 * 60 * 1000L;

    private static final String[] AUDIO_EXTENSIONS = {
        ".mp3",
        ".m4a",
        ".aac",
        ".flac",
        ".ogg",
        ".opus",
        ".wav"
    };

    private ExoPlayer player;
    private MediaLibrarySession session;
    private LibrarySnapshot snapshot = LibrarySnapshot.empty();

    @Override
    public void onCreate() {
        super.onCreate();
        player = new ExoPlayer.Builder(this).build();
        session = new MediaLibrarySession.Builder(
            this,
            player,
            new AutoSessionCallback()
        )
            .setId("downtify-auto")
            .build();
    }

    @Nullable
    @Override
    public MediaLibrarySession onGetSession(
        @NonNull MediaSession.ControllerInfo controllerInfo
    ) {
        return session;
    }

    @Override
    public void onTaskRemoved(@Nullable Intent rootIntent) {
        if (player != null && !player.getPlayWhenReady()) {
            stopSelf();
        }
    }

    @Override
    public void onDestroy() {
        if (session != null) {
            session.release();
            session = null;
        }
        if (player != null) {
            player.release();
            player = null;
        }
        super.onDestroy();
    }

    private synchronized LibrarySnapshot library() {
        long now = System.currentTimeMillis();
        if (now - snapshot.createdAtMs > LIBRARY_CACHE_MS) {
            snapshot = LibrarySnapshot.scan(
                new File(EmbeddedServerPlugin.defaultDownloadDir(this))
            );
        }
        return snapshot;
    }

    private final class AutoSessionCallback
        implements MediaLibrarySession.Callback {

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<MediaItem>> onGetLibraryRoot(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @Nullable LibraryParams params
        ) {
            return Futures.immediateFuture(LibraryResult.ofItem(rootItem(), params));
        }

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<ImmutableList<MediaItem>>> onGetChildren(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String parentId,
            int page,
            int pageSize,
            @Nullable LibraryParams params
        ) {
            List<MediaItem> children = childrenFor(parentId);
            return Futures.immediateFuture(
                LibraryResult.ofItemList(paged(children, page, pageSize), params)
            );
        }

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<MediaItem>> onGetItem(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String mediaId
        ) {
            MediaItem item = itemFor(mediaId);
            if (item == null) {
                return Futures.immediateFuture(
                    LibraryResult.ofError(LibraryResult.RESULT_ERROR_BAD_VALUE)
                );
            }
            return Futures.immediateFuture(LibraryResult.ofItem(item, null));
        }

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<Void>> onSearch(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String query,
            @Nullable LibraryParams params
        ) {
            return Futures.immediateFuture(LibraryResult.ofVoid(params));
        }

        @NonNull
        @Override
        public ListenableFuture<LibraryResult<ImmutableList<MediaItem>>> onGetSearchResult(
            @NonNull MediaLibrarySession session,
            @NonNull MediaSession.ControllerInfo browser,
            @NonNull String query,
            int page,
            int pageSize,
            @Nullable LibraryParams params
        ) {
            String needle = normalize(query);
            List<MediaItem> matches = new ArrayList<>();
            for (Track track : library().tracks) {
                if (
                    normalize(track.title).contains(needle) ||
                    normalize(track.artist).contains(needle) ||
                    normalize(track.album).contains(needle)
                ) {
                    matches.add(track.toPlayableItem());
                }
            }
            return Futures.immediateFuture(
                LibraryResult.ofItemList(paged(matches, page, pageSize), params)
            );
        }

        @NonNull
        @Override
        public ListenableFuture<List<MediaItem>> onAddMediaItems(
            @NonNull MediaSession session,
            @NonNull MediaSession.ControllerInfo controller,
            @NonNull List<MediaItem> mediaItems
        ) {
            List<MediaItem> playable = new ArrayList<>();
            LibrarySnapshot current = library();
            for (MediaItem item : mediaItems) {
                Track track = current.byId.get(item.mediaId);
                if (track != null) {
                    playable.add(track.toPlayableItem());
                } else if (item.mediaId.startsWith(ARTIST_PREFIX)) {
                    playable.addAll(playableTracks(current.byArtist.get(item.mediaId)));
                } else if (item.mediaId.startsWith(ALBUM_PREFIX)) {
                    playable.addAll(playableTracks(current.byAlbum.get(item.mediaId)));
                } else if (item.localConfiguration != null) {
                    playable.add(item);
                }
            }
            return Futures.immediateFuture(playable);
        }

    }

    private MediaItem rootItem() {
        return browsable(ROOT_ID, getString(getApplicationInfo().labelRes), null, false);
    }

    private MediaItem itemFor(String mediaId) {
        if (ROOT_ID.equals(mediaId)) return rootItem();
        if (ARTISTS_ID.equals(mediaId)) return browsable(ARTISTS_ID, "Artists", null, false);
        if (ALBUMS_ID.equals(mediaId)) return browsable(ALBUMS_ID, "Albums", null, false);
        if (TRACKS_ID.equals(mediaId)) return browsable(TRACKS_ID, "Tracks", null, false);

        LibrarySnapshot current = library();
        Track track = current.byId.get(mediaId);
        if (track != null) return track.toPlayableItem();

        if (mediaId.startsWith(ARTIST_PREFIX)) {
            String artist = current.artistNames.get(mediaId);
            if (artist != null) return browsable(mediaId, artist, null, true);
        }
        if (mediaId.startsWith(ALBUM_PREFIX)) {
            String album = current.albumNames.get(mediaId);
            if (album != null) return browsable(mediaId, album, null, true);
        }
        return null;
    }

    private List<MediaItem> childrenFor(String parentId) {
        LibrarySnapshot current = library();
        if (ROOT_ID.equals(parentId)) {
            List<MediaItem> roots = new ArrayList<>();
            roots.add(browsable(ARTISTS_ID, "Artists", "Browse by artist", false));
            roots.add(browsable(ALBUMS_ID, "Albums", "Browse by album", false));
            roots.add(browsable(TRACKS_ID, "Tracks", "All downloaded tracks", false));
            return roots;
        }
        if (ARTISTS_ID.equals(parentId)) {
            return new ArrayList<>(current.artistItems.values());
        }
        if (ALBUMS_ID.equals(parentId)) {
            return new ArrayList<>(current.albumItems.values());
        }
        if (TRACKS_ID.equals(parentId)) {
            List<MediaItem> tracks = new ArrayList<>();
            for (Track track : current.tracks) tracks.add(track.toPlayableItem());
            return tracks;
        }
        if (parentId.startsWith(ARTIST_PREFIX)) {
            return playableTracks(current.byArtist.get(parentId));
        }
        if (parentId.startsWith(ALBUM_PREFIX)) {
            return playableTracks(current.byAlbum.get(parentId));
        }
        return Collections.emptyList();
    }

    private List<MediaItem> playableTracks(List<Track> tracks) {
        if (tracks == null) return Collections.emptyList();
        List<MediaItem> items = new ArrayList<>();
        for (Track track : tracks) items.add(track.toPlayableItem());
        return items;
    }

    private ImmutableList<MediaItem> paged(
        List<MediaItem> items,
        int page,
        int pageSize
    ) {
        if (page < 0 || pageSize <= 0) {
            return ImmutableList.copyOf(items);
        }
        int from = page * pageSize;
        if (from >= items.size()) {
            return ImmutableList.of();
        }
        int to = Math.min(from + pageSize, items.size());
        return ImmutableList.copyOf(items.subList(from, to));
    }

    private static MediaItem browsable(
        String mediaId,
        String title,
        @Nullable String subtitle,
        boolean playable
    ) {
        MediaMetadata.Builder metadata = new MediaMetadata.Builder()
            .setTitle(title)
            .setIsBrowsable(true)
            .setIsPlayable(playable)
            .setMediaType(MediaMetadata.MEDIA_TYPE_FOLDER_MIXED);
        if (subtitle != null) metadata.setSubtitle(subtitle);
        return new MediaItem.Builder()
            .setMediaId(mediaId)
            .setMediaMetadata(metadata.build())
            .build();
    }

    private static boolean isAudioFile(File file) {
        String name = file.getName().toLowerCase(Locale.US);
        for (String extension : AUDIO_EXTENSIONS) {
            if (name.endsWith(extension)) return true;
        }
        return false;
    }

    private static void collectAudioFiles(File dir, List<File> files) {
        File[] children = dir.listFiles();
        if (children == null) return;
        for (File child : children) {
            if (child.isDirectory()) {
                collectAudioFiles(child, files);
            } else if (child.isFile() && isAudioFile(child)) {
                files.add(child);
            }
        }
    }

    private static String normalize(String value) {
        String base = value == null ? "" : value;
        return Normalizer.normalize(base, Normalizer.Form.NFD)
            .replaceAll("\\p{InCombiningDiacriticalMarks}+", "")
            .toLowerCase(Locale.US)
            .trim();
    }

    private static String safeIdPart(String value) {
        String normalized = normalize(value);
        return normalized.replaceAll("[^a-z0-9]+", "-").replaceAll("(^-|-$)", "");
    }

    private static final class Track {

        final File file;
        final String mediaId;
        final String title;
        final String artist;
        final String album;
        final long durationMs;

        Track(File file) {
            this.file = file;
            String fileTitle = file.getName().replaceFirst("\\.[^.]+$", "");
            String foundTitle = fileTitle;
            String foundArtist = "Unknown artist";
            String foundAlbum = "Unknown album";
            long foundDurationMs = C.TIME_UNSET;

            MediaMetadataRetriever retriever = new MediaMetadataRetriever();
            try {
                retriever.setDataSource(file.getAbsolutePath());
                foundTitle =
                    clean(
                        retriever.extractMetadata(
                            MediaMetadataRetriever.METADATA_KEY_TITLE
                        ),
                        fileTitle
                    );
                foundArtist =
                    clean(
                        retriever.extractMetadata(
                            MediaMetadataRetriever.METADATA_KEY_ARTIST
                        ),
                        "Unknown artist"
                    );
                foundAlbum =
                    clean(
                        retriever.extractMetadata(
                            MediaMetadataRetriever.METADATA_KEY_ALBUM
                        ),
                        "Unknown album"
                    );
                String duration =
                    retriever.extractMetadata(
                        MediaMetadataRetriever.METADATA_KEY_DURATION
                    );
                if (duration != null) {
                    foundDurationMs = Long.parseLong(duration);
                }
            } catch (Exception ignored) {
                // Metadata is helpful but not required for Android Auto playback.
            } finally {
                try {
                    retriever.release();
                } catch (Exception ignored) {}
            }

            title = foundTitle;
            artist = foundArtist;
            album = foundAlbum;
            durationMs = foundDurationMs;
            mediaId = TRACK_PREFIX + Uri.encode(file.getAbsolutePath());
        }

        MediaItem toPlayableItem() {
            MediaMetadata.Builder metadata = new MediaMetadata.Builder()
                .setTitle(title)
                .setArtist(artist)
                .setAlbumTitle(album)
                .setIsBrowsable(false)
                .setIsPlayable(true)
                .setMediaType(MediaMetadata.MEDIA_TYPE_MUSIC);
            if (durationMs > 0) metadata.setDurationMs(durationMs);
            return new MediaItem.Builder()
                .setMediaId(mediaId)
                .setUri(Uri.fromFile(file))
                .setMediaMetadata(metadata.build())
                .build();
        }

        private static String clean(String value, String fallback) {
            String trimmed = value == null ? "" : value.trim();
            return trimmed.isEmpty() ? fallback : trimmed;
        }
    }

    private static final class LibrarySnapshot {

        final long createdAtMs;
        final List<Track> tracks;
        final Map<String, Track> byId;
        final Map<String, MediaItem> artistItems;
        final Map<String, MediaItem> albumItems;
        final Map<String, String> artistNames;
        final Map<String, String> albumNames;
        final Map<String, List<Track>> byArtist;
        final Map<String, List<Track>> byAlbum;

        LibrarySnapshot(
            long createdAtMs,
            List<Track> tracks,
            Map<String, Track> byId,
            Map<String, MediaItem> artistItems,
            Map<String, MediaItem> albumItems,
            Map<String, String> artistNames,
            Map<String, String> albumNames,
            Map<String, List<Track>> byArtist,
            Map<String, List<Track>> byAlbum
        ) {
            this.createdAtMs = createdAtMs;
            this.tracks = tracks;
            this.byId = byId;
            this.artistItems = artistItems;
            this.albumItems = albumItems;
            this.artistNames = artistNames;
            this.albumNames = albumNames;
            this.byArtist = byArtist;
            this.byAlbum = byAlbum;
        }

        static LibrarySnapshot empty() {
            return new LibrarySnapshot(
                0L,
                Collections.emptyList(),
                Collections.emptyMap(),
                Collections.emptyMap(),
                Collections.emptyMap(),
                Collections.emptyMap(),
                Collections.emptyMap(),
                Collections.emptyMap(),
                Collections.emptyMap()
            );
        }

        static LibrarySnapshot scan(File root) {
            List<File> files = new ArrayList<>();
            if (root.isDirectory()) collectAudioFiles(root, files);
            files.sort(Comparator.comparing(File::getAbsolutePath));

            List<Track> tracks = new ArrayList<>();
            Map<String, Track> byId = new LinkedHashMap<>();
            Map<String, MediaItem> artistItems = new LinkedHashMap<>();
            Map<String, MediaItem> albumItems = new LinkedHashMap<>();
            Map<String, String> artistNames = new LinkedHashMap<>();
            Map<String, String> albumNames = new LinkedHashMap<>();
            Map<String, List<Track>> byArtist = new LinkedHashMap<>();
            Map<String, List<Track>> byAlbum = new LinkedHashMap<>();

            for (File file : files) {
                Track track = new Track(file);
                tracks.add(track);
                byId.put(track.mediaId, track);

                String artistId = ARTIST_PREFIX + safeIdPart(track.artist);
                String albumId =
                    ALBUM_PREFIX +
                    safeIdPart(track.album) +
                    ":" +
                    safeIdPart(track.artist);

                artistNames.putIfAbsent(artistId, track.artist);
                albumNames.putIfAbsent(albumId, track.album);
                byArtist.computeIfAbsent(artistId, ignored -> new ArrayList<>()).add(track);
                byAlbum.computeIfAbsent(albumId, ignored -> new ArrayList<>()).add(track);
            }

            List<String> artistIds = new ArrayList<>(artistNames.keySet());
            artistIds.sort(
                Comparator.comparing(id -> normalize(artistNames.get(id)))
            );
            for (String id : artistIds) {
                List<Track> artistTracks = byArtist.get(id);
                String subtitle =
                    artistTracks == null || artistTracks.size() == 1
                        ? "1 track"
                        : artistTracks.size() + " tracks";
                artistItems.put(id, browsable(id, artistNames.get(id), subtitle, true));
                sortTracks(artistTracks);
            }

            List<String> albumIds = new ArrayList<>(albumNames.keySet());
            albumIds.sort(Comparator.comparing(id -> normalize(albumNames.get(id))));
            for (String id : albumIds) {
                List<Track> albumTracks = byAlbum.get(id);
                String artist = albumTracks == null || albumTracks.isEmpty()
                    ? null
                    : albumTracks.get(0).artist;
                albumItems.put(id, browsable(id, albumNames.get(id), artist, true));
                sortTracks(albumTracks);
            }

            sortTracks(tracks);
            return new LibrarySnapshot(
                System.currentTimeMillis(),
                tracks,
                byId,
                artistItems,
                albumItems,
                artistNames,
                albumNames,
                byArtist,
                byAlbum
            );
        }

        private static void sortTracks(List<Track> tracks) {
            if (tracks == null) return;
            tracks.sort(
                Comparator.comparing((Track track) -> normalize(track.artist))
                    .thenComparing(track -> normalize(track.album))
                    .thenComparing(track -> normalize(track.title))
            );
        }
    }
}
