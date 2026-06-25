"""Download a track from YouTube and tag it with the chosen metadata."""

from __future__ import annotations

import os
import re
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

import requests
from loguru import logger
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3
from mutagen.id3._frames import (
    APIC,
    TALB,
    TCON,
    TDOR,
    TDRC,
    TIT2,
    TPE1,
    TPE2,
    TPOS,
    TRCK,
    TXXX,
    USLT,
)
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from . import lyrics as lyrics_mod
from .artist_art import (
    artist_or_fallback_image,
    resolve_artist_mbid,
    save_artist_images_for_track,
)
from .audio_caps import ffmpeg_available as _ffmpeg_available
from .genres import canonical_genre
from .jellyfin_meta import format_for_jellyfin
from .m3u import sanitize_playlist_name
from .musicbrainz import enrich_song_metadata
from .providers import enrich_from_match, find_match, find_match_for_video

if TYPE_CHECKING:
    import yt_dlp as yt_dlp_module


def _yt_dlp() -> 'yt_dlp_module':
    """Import yt-dlp lazily.

    yt-dlp pulls in a very large set of extractor modules at import time, which
    is slow on the embedded Android (Chaquopy) build. Deferring the import to
    first use lets the server become responsive (search, library, playback)
    without paying that cost up front; only the first download/preview pays it.
    """

    import yt_dlp

    return yt_dlp


_INVALID_FS_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_AUDIO_EXTENSIONS = {'mp3', 'm4a', 'mp4', 'aac', 'flac', 'ogg', 'opus', 'wav'}
# AAC in an MP4/M4A container is the one codec every ffmpeg build (including the
# minimal static binary bundled in the Android APK) can reliably produce, so it
# is used as a fallback when the configured codec cannot be encoded on-device.
_FALLBACK_AUDIO_FORMAT = 'm4a'

# Prefer a natively downloadable AAC/M4A stream so a playable, taggable file can
# be produced without any ffmpeg post-processing (used on builds with no ffmpeg,
# e.g. the embedded Android APK). Falls back to whatever audio is available.
_NATIVE_AUDIO_FORMAT = (
    'bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/best[ext=m4a]/bestaudio/best'
)


ProgressCallback = Callable[[float, str], None]
_PREVIEW_AUDIO_CACHE_TTL_SECONDS = 45 * 60
_PREVIEW_AUDIO_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _sanitize(text: str) -> str:
    safe = _INVALID_FS_CHARS.sub('', text or '').strip().strip('.')
    return safe or 'unknown'


def _normalize_duplicate_key(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', text.lower())


_DEFAULT_YT_PLAYER_CLIENTS = (
    'ios',
    'android',
    'web_embedded',
    'mweb',
    'web',
    'tv',
)

_SUPPRESSED_YT_WARNING_FRAGMENTS = (
    'GVS PO Token which was not provided',
    'Some tv client https formats have been skipped as they are DRM',
    'Signature solving failed: Some formats may be missing',
    'n challenge solving failed: Some formats may be missing',
)


class _YtdlpLogger:
    @staticmethod
    def debug(msg: str) -> None:
        pass

    @staticmethod
    def info(msg: str) -> None:
        pass

    @staticmethod
    def warning(msg: str) -> None:
        if not any(frag in msg for frag in _SUPPRESSED_YT_WARNING_FRAGMENTS):
            logger.warning('yt-dlp: {}', msg)

    @staticmethod
    def error(msg: str) -> None:
        logger.error('yt-dlp: {}', msg)


def _yt_player_clients() -> list[str]:
    raw = os.getenv('DOWNTIFY_YT_PLAYER_CLIENTS', '').strip()
    if not raw:
        return list(_DEFAULT_YT_PLAYER_CLIENTS)
    clients = [c.strip() for c in raw.split(',') if c.strip()]
    return clients or list(_DEFAULT_YT_PLAYER_CLIENTS)


def _base_ytdlp_opts() -> dict[str, Any]:
    ydl_opts: dict[str, Any] = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noprogress': True,
        'logger': _YtdlpLogger(),
        'noplaylist': True,
        'nocheckcertificate': True,
        'retries': 10,
        'fragment_retries': 10,
        'extractor_retries': 3,
        'socket_timeout': 30,
        'extractor_args': {
            'youtube': {'player_client': _yt_player_clients()}
        },
        'sleep_interval_requests': 1,
    }

    if os.getenv('DOWNTIFY_FORCE_IPV4', '').strip() in {
        '1',
        'true',
        'yes',
    }:
        ydl_opts['source_address'] = '0.0.0.0'

    cookies_file = os.getenv('DOWNTIFY_COOKIES_FILE', '').strip()
    if cookies_file:
        ydl_opts['cookiefile'] = cookies_file

    cookies_browser = os.getenv('DOWNTIFY_COOKIES_FROM_BROWSER', '').strip()
    if cookies_browser:
        parts = cookies_browser.split(':', 1)
        ydl_opts['cookiesfrombrowser'] = (
            (parts[0],) if len(parts) == 1 else (parts[0], parts[1])
        )

    # On platforms where ffmpeg is not on PATH (e.g. the embedded Android
    # build, which bundles its own binary) the location can be provided
    # explicitly so yt-dlp's post-processing can find it.
    ffmpeg_location = os.getenv('DOWNTIFY_FFMPEG_LOCATION', '').strip()
    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location

    return ydl_opts


def _resolve_youtube_match(
    song: dict[str, Any],
) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    video_id = song.get('youtube_id')
    if not video_id and (song.get('source') == 'youtube'):
        song_id = str(song.get('song_id') or '').strip()
        if song_id and not song_id.startswith('album:'):
            video_id = song_id

    match: Optional[dict[str, Any]] = None
    if not video_id:
        video_id, match = find_match(song)
    elif not song.get('album_name') or not song.get('cover_url'):
        try:
            match = find_match_for_video(song, video_id)
        except Exception:
            logger.opt(exception=True).debug('enrichment match failed')
            match = None

    return video_id, match


def _best_audio_url(info: dict[str, Any]) -> str:
    requested = info.get('requested_downloads') or []
    for item in requested:
        if item.get('url'):
            return item['url']

    if info.get('url'):
        return info['url']

    formats = [
        fmt
        for fmt in (info.get('formats') or [])
        if fmt.get('url') and fmt.get('acodec') != 'none'
    ]
    formats.sort(key=lambda fmt: fmt.get('abr') or fmt.get('tbr') or 0)
    return formats[-1]['url'] if formats else ''


def _preview_cache_key(song: dict[str, Any]) -> str:
    return str(
        song.get('youtube_id')
        or song.get('song_id')
        or song.get('url')
        or f"{song.get('name', '')}:{','.join(song.get('artists') or [])}"
    )


def preview_audio_for_song(song: dict[str, Any]) -> dict[str, Any]:
    cache_key = _preview_cache_key(song)
    cached = _PREVIEW_AUDIO_CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _PREVIEW_AUDIO_CACHE_TTL_SECONDS:
        return cached[1]

    video_id, match = _resolve_youtube_match(song)
    if not video_id:
        raise RuntimeError(
            f'Could not find a YouTube match for {song.get("name")!r}'
        )

    ydl_opts = _base_ytdlp_opts()
    ydl_opts['skip_download'] = True

    url = f'https://music.youtube.com/watch?v={video_id}'
    with _yt_dlp().YoutubeDL(cast(Any, ydl_opts)) as ydl:
        info = ydl.extract_info(url, download=False)

    audio_url = _best_audio_url(cast(dict[str, Any], info or {}))
    if not audio_url:
        raise RuntimeError(
            f'Could not resolve a playable preview for {song.get("name")!r}'
        )

    result = {
        'video_id': video_id,
        'audio_url': audio_url,
        'track': enrich_from_match(song, match),
    }
    _PREVIEW_AUDIO_CACHE[cache_key] = (time.time(), result)
    return result


class Downloader:
    """Wraps ``yt-dlp`` plus ``mutagen`` tagging."""

    def __init__(
        self,
        download_dir: Path | str,
        audio_format: str = 'mp3',
        audio_bitrate: str = '320',
        output_template: str = '{artists} - {title}',
        lyrics_providers: Optional[list[str]] = None,
        organize_by_artist: bool = False,
        organize_by_album: bool = False,
        enhance_metadata: bool = True,
        download_artist_images: bool = True,
        artist_folder_policy: str = 'artwork_available',
        discogs_token: str = '',
    ):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.audio_format = audio_format
        self.audio_bitrate = audio_bitrate
        self.output_template = output_template
        self.lyrics_providers = list(lyrics_providers or [])
        self.organize_by_artist = organize_by_artist
        self.organize_by_album = organize_by_album
        self.enhance_metadata = enhance_metadata
        self.download_artist_images = download_artist_images
        self.artist_folder_policy = artist_folder_policy
        self.discogs_token = discogs_token

    @staticmethod
    def _artist_subdir(song: dict[str, Any]) -> str:
        artists = song.get('artists') or []
        return _sanitize(artists[0] if artists else 'unknown')

    @staticmethod
    def _album_subdir(song: dict[str, Any]) -> str:
        album = (song.get('album_name') or '').strip()
        return _sanitize(album) if album else 'Unknown Album'

    def _content_subdir(
        self,
        song: dict[str, Any],
        subdir: Optional[str] = None,
    ) -> Optional[str]:
        if self.organize_by_artist:
            parts = [self._artist_subdir(song)]
            if self.organize_by_album:
                parts.append(self._album_subdir(song))
            return '/'.join(parts)
        return subdir

    def _format_basename(self, song: dict[str, Any]) -> str:
        artists = ', '.join(song.get('artists') or []) or 'Unknown Artist'
        # BUG FIX 1: The original `.replace('.{output-ext}', '')` used a hyphen
        # in the placeholder, making it an invalid Python format identifier that
        # str.format() would raise on.  Strip the yt-dlp extension token instead.
        template = self.output_template.replace('.%(ext)s', '').replace('%(ext)s', '')
        try:
            rendered = template.format(
                title=song.get('name', 'Unknown'),
                artists=artists,
                artist=artists,
                album=song.get('album_name', ''),
            )
        except (KeyError, IndexError):
            rendered = f'{artists} - {song.get("name", "Unknown")}'
        return _sanitize(rendered)

    def existing_filename_for(
        self,
        song: dict[str, Any],
        subdir: Optional[str] = None,
    ) -> Optional[str]:
        basename = self._format_basename(song)
        effective_subdir = self._content_subdir(song, subdir)
        target_dir, prefix = self._resolve_target_dir(effective_subdir)
        primary = target_dir / f'{basename}.{self.audio_format}'
        if primary.exists():
            return f'{prefix}{primary.name}'
        for candidate in target_dir.glob(f'{basename}.*'):
            if candidate.is_file():
                return f'{prefix}{candidate.name}'
        return None

    def duplicate_filename_for(
        self,
        song: dict[str, Any],
        subdir: Optional[str] = None,
    ) -> Optional[str]:
        hit = self._duplicate_filename_for_song(song, subdir=subdir)
        if hit:
            return hit

        artists = song.get('artists') or []
        if len(artists) <= 1:
            return None
        for artist in artists:
            name = str(artist or '').strip()
            if not name:
                continue
            solo = {**song, 'artists': [name]}
            hit = self._duplicate_filename_for_song(solo, subdir=subdir)
            if hit:
                return hit
        return None

    def _duplicate_filename_for_song(
        self,
        song: dict[str, Any],
        subdir: Optional[str] = None,
    ) -> Optional[str]:
        exact = self.existing_filename_for(song, subdir=subdir)
        if (
            exact
            and Path(exact).suffix.lower().lstrip('.') in _AUDIO_EXTENSIONS
        ):
            return exact

        basename_key = _normalize_duplicate_key(self._format_basename(song))
        if not basename_key:
            return None

        for candidate in self.download_dir.rglob('*'):
            if not candidate.is_file():
                continue
            if candidate.suffix.lower().lstrip('.') not in _AUDIO_EXTENSIONS:
                continue
            if _normalize_duplicate_key(candidate.stem) == basename_key:
                return candidate.relative_to(self.download_dir).as_posix()
        return None

    def _resolve_target_dir(self, subdir: Optional[str]) -> tuple[Path, str]:
        if not subdir:
            return self.download_dir, ''
        parts = [
            sanitize_playlist_name(part)
            for part in subdir.replace('\\', '/').split('/')
            if part.strip()
        ]
        if not parts:
            return self.download_dir, ''
        target = self.download_dir
        for part in parts:
            target = target / part
        return target, f"{'/'.join(parts)}/"

    def _extract_opts(
        self,
        out_template: str,
        hook: Callable[[dict[str, Any]], None],
        audio_format: str,
    ) -> dict[str, Any]:
        ydl_opts = _base_ytdlp_opts()
        ydl_opts.update({
            'outtmpl': out_template,
            'overwrites': True,
            'progress_hooks': [hook],
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': self.audio_bitrate,
                }
            ],
        })
        return ydl_opts

    @staticmethod
    def _cleanup_leftovers(
        target_dir: Path, basename: str, keep: Path
    ) -> None:
        """Remove stray same-basename source containers (e.g. a leftover
        ``.webm``/``.mp4`` from a failed first conversion attempt)."""

        for candidate in target_dir.glob(f'{basename}.*'):
            if candidate == keep or not candidate.is_file():
                continue
            if candidate.suffix.lower() in {'.lrc', '.txt'}:
                continue
            try:
                candidate.unlink()
            except OSError:
                logger.opt(exception=True).debug(
                    'Could not remove leftover {}', candidate
                )

    def _download_native_audio(
        self,
        url: str,
        out_template: str,
        target_dir: Path,
        basename: str,
        hook: Callable[[dict[str, Any]], None],
    ) -> Path:
        """Download a playable audio container with no ffmpeg post-processing.

        Used on builds without ffmpeg (e.g. the embedded Android APK). The file
        is later tagged — including embedded cover art — by mutagen, which needs
        no external binaries, so downloads succeed and covers render on-device.
        """

        ydl_opts = _base_ytdlp_opts()
        ydl_opts.update({
            'outtmpl': out_template,
            'overwrites': True,
            'progress_hooks': [hook],
            'format': _NATIVE_AUDIO_FORMAT,
            'postprocessors': [],
        })
        with _yt_dlp().YoutubeDL(cast(Any, ydl_opts)) as ydl:
            ydl.download([url])

        chosen: Optional[Path] = None
        for candidate in sorted(target_dir.glob(f'{basename}.*')):
            if not candidate.is_file():
                continue
            if candidate.suffix.lower().lstrip('.') in _AUDIO_EXTENSIONS:
                chosen = candidate
                break
        if chosen is None:
            for candidate in target_dir.glob(f'{basename}.*'):
                if candidate.is_file():
                    chosen = candidate
                    break
        if chosen is None:
            return target_dir / f'{basename}.{_FALLBACK_AUDIO_FORMAT}'
        self._cleanup_leftovers(target_dir, basename, keep=chosen)
        return chosen

    def _download_and_extract(
        self,
        url: str,
        out_template: str,
        target_dir: Path,
        basename: str,
        hook: Callable[[dict[str, Any]], None],
    ) -> Path:
        """Download a track and extract audio to the configured format.

        When no ffmpeg binary is available (e.g. the embedded Android APK), skip
        post-processing entirely and keep a natively downloaded AAC/M4A file so
        the download still succeeds. Otherwise extract to the configured format,
        falling back to ``m4a`` (AAC) when the configured codec cannot be
        produced on this platform, so the user still gets a tagged, playable,
        library-visible file.
        """

        if not _ffmpeg_available():
            logger.info(
                'ffmpeg unavailable; downloading native audio without '
                'conversion for {}',
                basename,
            )
            return self._download_native_audio(
                url, out_template, target_dir, basename, hook
            )

        primary = (self.audio_format or 'mp3').lower()
        try:
            with _yt_dlp().YoutubeDL(
                cast(Any, self._extract_opts(out_template, hook, primary))
            ) as ydl:
                ydl.download([url])
        except Exception as exc:
            if primary == _FALLBACK_AUDIO_FORMAT:
                raise
            logger.warning(
                "Audio extraction to {!r} failed ({}); retrying as {!r}.",
                primary,
                exc,
                _FALLBACK_AUDIO_FORMAT,
            )
            self._cleanup_leftovers(
                target_dir, basename, keep=target_dir / basename
            )
            with _yt_dlp().YoutubeDL(
                cast(
                    Any,
                    self._extract_opts(
                        out_template, hook, _FALLBACK_AUDIO_FORMAT
                    ),
                )
            ) as ydl:
                ydl.download([url])

        for ext in (primary, _FALLBACK_AUDIO_FORMAT):
            candidate = target_dir / f'{basename}.{ext}'
            if candidate.exists():
                self._cleanup_leftovers(target_dir, basename, keep=candidate)
                return candidate

        for candidate in target_dir.glob(f'{basename}.*'):
            if candidate.is_file():
                return candidate
        return target_dir / f'{basename}.{primary}'

    def download(
        self,
        song: dict[str, Any],
        progress_cb: Optional[ProgressCallback] = None,
        subdir: Optional[str] = None,
    ) -> str:
        video_id, match = _resolve_youtube_match(song)

        if not video_id:
            raise RuntimeError(
                f'Could not find a YouTube match for {song.get("name")!r}'
            )

        song = enrich_from_match(song, match)
        if self.enhance_metadata:
            song = enrich_song_metadata(song)

        basename = self._format_basename(song)
        effective_subdir = self._content_subdir(song, subdir)
        target_dir, rel_prefix = self._resolve_target_dir(effective_subdir)
        target_dir.mkdir(parents=True, exist_ok=True)
        out_template = str(target_dir / f'{basename}.%(ext)s')

        def hook(data: dict[str, Any]) -> None:
            if progress_cb is None:
                return
            try:
                status = data.get('status')
                if status == 'downloading':
                    total = (
                        data.get('total_bytes')
                        or data.get('total_bytes_estimate')
                        or 0
                    )
                    downloaded = data.get('downloaded_bytes') or 0
                    if total:
                        progress_cb(
                            min(95.0, downloaded / total * 95.0),
                            'Downloading',
                        )
                elif status == 'finished':
                    progress_cb(96.0, 'Converting')
            except Exception:
                logger.opt(exception=True).debug('progress hook error')

        url = f'https://music.youtube.com/watch?v={video_id}'
        final_path = self._download_and_extract(
            url, out_template, target_dir, basename, hook
        )

        try:
            embed_metadata(final_path, song)
        except Exception:
            logger.exception('Failed to embed metadata into {}', final_path)

        if self.lyrics_providers:
            try:
                fetched = lyrics_mod.fetch(song, self.lyrics_providers)
            except Exception:
                logger.exception('Lyrics fetch crashed for {}', final_path)
                fetched = None
            if fetched is not None:
                try:
                    embed_lyrics(final_path, fetched)
                except Exception:
                    logger.exception(
                        'Failed to embed lyrics into {}', final_path
                    )

        self._maybe_save_artist_images(final_path, song)

        if progress_cb:
            progress_cb(100.0, 'Done')
        return f'{rel_prefix}{final_path.name}'

    def _maybe_save_artist_images(
        self, final_path: Path, song: dict[str, Any]
    ) -> None:
        """Fetch and cache real artist photos for the track's artists.

        Runs in a background thread so it never delays the download finishing.
        Artist photos are a separate asset from embedded album art and are the
        only way the library's artist tiles can show real headshots — without
        this they fall back to album covers. Best-effort and non-fatal.
        """

        if not self.download_artist_images:
            return
        names = song.get('artists') or []
        if not names:
            single = str(song.get('artist') or '').strip()
            names = [single] if single else []
        artists = [
            {'name': str(name).strip(), 'id': ''}
            for name in names
            if str(name).strip()
        ]
        if not artists:
            return

        thread = threading.Thread(
            target=self._save_artist_images,
            args=(final_path, artists),
            daemon=True,
        )
        thread.start()

    def _save_artist_images(
        self, final_path: Path, artists: list[dict[str, str]]
    ) -> None:
        from . import artist_image_sources

        def image_for_artist(
            artist: dict[str, str],
        ) -> tuple[Optional[bytes], str]:
            name = artist.get('name', '')
            if name:
                try:
                    data, source = artist_image_sources.fetch_online_artist_image(
                        name, discogs_token=self.discogs_token
                    )
                    if data:
                        return data, source
                except Exception:
                    logger.opt(exception=True).debug(
                        'online artist image lookup failed for {!r}', name
                    )
            try:
                return artist_or_fallback_image(
                    resolve_artist_mbid(artist, final_path), final_path
                )
            except Exception:
                return None, ''

        try:
            saved = save_artist_images_for_track(
                self.download_dir,
                final_path,
                artists,
                image_for_artist,
                artist_folder_policy=self.artist_folder_policy,
            )
            if saved:
                logger.info('Saved artist image(s): {}', ', '.join(saved))
        except Exception:
            logger.opt(exception=True).warning(
                'Failed to save artist images for {}', final_path
            )


def _download_cover(url: str) -> Optional[bytes]:
    if not url:
        return None
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except Exception:
        logger.opt(exception=True).warning('Failed to fetch cover art {}', url)
        return None
    return response.content


def _album_track_index_for_tags(
    song: dict[str, Any],
) -> tuple[Optional[int], Optional[int]]:
    raw_n = song.get('track_number')
    raw_tot = song.get('album_track_total')
    if raw_n is None:
        return None, None
    try:
        n = int(raw_n)
    except (TypeError, ValueError):
        return None, None
    if n <= 0:
        return None, None
    tot: Optional[int] = None
    if raw_tot is not None and raw_tot != '':
        try:
            t = int(raw_tot)
        except (TypeError, ValueError):
            pass
        else:
            if t > 0:
                tot = t
    return n, tot


def _recording_date_for_tags(song: dict[str, Any]) -> str:
    rd = str(song.get('release_date') or '').strip()
    if rd:
        return rd
    return str(song.get('year') or '').strip()


def embed_metadata(path: Path, song: dict[str, Any]) -> None:
    if not path.exists():
        return

    song = format_for_jellyfin(song)

    title = song.get('name', '')
    artists = song.get('artists') or []
    album = song.get('album_name', '') or ''
    recording_date = _recording_date_for_tags(song)
    genre = canonical_genre((song.get('genre') or '').strip())
    cover_bytes = _download_cover(song.get('cover_url', ''))
    track_number, album_track_total = _album_track_index_for_tags(song)
    album_artist = song.get('album_artist')
    disc_number = song.get('disc_number')
    disc_total = song.get('disc_total')
    compilation = bool(song.get('compilation'))

    if track_number is None:
        logger.info(
            'Tag embed: no track_number/disc position for file={} song_id={} '
            'title={!r} raw_track_number={!r} raw_total={!r}',
            path.name,
            song.get('song_id'),
            title,
            song.get('track_number'),
            song.get('album_track_total'),
        )
    if not recording_date:
        logger.info(
            'Tag embed: no recording date (year/release_date) for file={} '
            'song_id={} title={!r} raw_year={!r} raw_release_date={!r}',
            path.name,
            song.get('song_id'),
            title,
            song.get('year'),
            song.get('release_date'),
        )

    logger.debug(
        'Tag embed summary: {} track={}/{} date={!r}',
        path.name,
        track_number,
        album_track_total,
        recording_date,
    )

    suffix = path.suffix.lower().lstrip('.')

    if suffix == 'mp3':
        _tag_mp3(
            path,
            title,
            artists,
            album,
            recording_date,
            genre,
            cover_bytes,
            track_number,
            album_track_total,
            album_artist=album_artist,
            disc_number=disc_number,
            disc_total=disc_total,
            compilation=compilation,
        )
    elif suffix in {'m4a', 'mp4', 'aac'}:
        _tag_mp4(
            path,
            title,
            artists,
            album,
            recording_date,
            genre,
            cover_bytes,
            track_number,
            album_track_total,
            album_artist=album_artist,
            disc_number=disc_number,
            disc_total=disc_total,
            compilation=compilation,
        )
    elif suffix == 'flac':
        _tag_flac(
            path,
            title,
            artists,
            album,
            recording_date,
            genre,
            cover_bytes,
            track_number,
            album_track_total,
            album_artist=album_artist,
            disc_number=disc_number,
            disc_total=disc_total,
            compilation=compilation,
        )
    elif suffix in {'ogg', 'oga'}:
        _tag_ogg_vorbis(
            path,
            title,
            artists,
            album,
            recording_date,
            genre,
            cover_bytes,
            track_number,
            album_track_total,
            album_artist=album_artist,
            disc_number=disc_number,
            disc_total=disc_total,
            compilation=compilation,
        )
    elif suffix == 'opus':
        _tag_opus(
            path,
            title,
            artists,
            album,
            recording_date,
            genre,
            cover_bytes,
            track_number,
            album_track_total,
            album_artist=album_artist,
            disc_number=disc_number,
            disc_total=disc_total,
            compilation=compilation,
        )


def _tag_mp3(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    year: str,
    genre: str,
    cover_bytes: Optional[bytes],
    track_number: Optional[int],
    album_track_total: Optional[int],
    album_artist: Optional[str] = None,
    disc_number: Optional[int] = None,
    disc_total: Optional[int] = None,
    compilation: bool = False,
) -> None:
    audio = MP3(str(path), ID3=ID3)
    if audio.tags is None:
        audio.add_tags()
    tags: ID3 = audio.tags  # type: ignore[assignment]  # add_tags() guarantees non-None
    tags.delall('APIC')
    tags.add(TIT2(encoding=3, text=title))
    if artists:
        tags.add(TPE1(encoding=3, text=' / '.join(artists)))
        tags.add(TPE2(encoding=3, text=album_artist or artists[0]))
        # BUG FIX 2: TXXX.text must be a list, not a null-byte-joined string.
        # Passing '\x00'.join(artists) embeds a single malformed string value
        # instead of the proper multi-value list that ID3 expects.
        tags.add(TXXX(encoding=3, desc='ARTISTS', text=artists))
    if album:
        tags.add(TALB(encoding=3, text=album))
    if track_number is not None:
        trck = (
            f'{track_number}/{album_track_total}'
            if album_track_total is not None
            else str(track_number)
        )
        tags.add(TRCK(encoding=3, text=trck))
    if disc_number is not None:
        tpos = (
            f'{disc_number}/{disc_total}'
            if disc_total is not None
            else str(disc_number)
        )
        tags.add(TPOS(encoding=3, text=tpos))
    if year:
        tags.add(TDRC(encoding=3, text=year))
        tags.add(TDOR(encoding=3, text=year[:4]))
    if genre:
        tags.add(TCON(encoding=3, text=genre))
    if compilation:
        tags.add(TXXX(encoding=3, desc='COMPILATION', text='1'))
    if cover_bytes:
        tags.add(
            APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover',
                data=cover_bytes,
            )
        )
    audio.save(v2_version=3)


def _tag_mp4(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    year: str,
    genre: str,
    cover_bytes: Optional[bytes],
    track_number: Optional[int],
    album_track_total: Optional[int],
    album_artist: Optional[str] = None,
    disc_number: Optional[int] = None,
    disc_total: Optional[int] = None,
    compilation: bool = False,
) -> None:
    audio = MP4(str(path))
    audio['\xa9nam'] = title
    if artists:
        audio['\xa9ART'] = artists
        audio['aART'] = [album_artist or artists[0]]
    if album:
        audio['\xa9alb'] = album
    if track_number is not None:
        total = album_track_total if album_track_total is not None else 0
        audio['trkn'] = [(track_number, total)]
    if disc_number is not None:
        total = disc_total if disc_total is not None else 0
        audio['disk'] = [(disc_number, total)]
    if year:
        audio['\xa9day'] = year
    if genre:
        audio['\xa9gen'] = genre
    if compilation:
        audio['cpil'] = [1]
    if cover_bytes:
        audio['covr'] = [
            MP4Cover(cover_bytes, imageformat=MP4Cover.FORMAT_JPEG)
        ]
    audio.save()


def _tag_flac(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    year: str,
    genre: str,
    cover_bytes: Optional[bytes],
    track_number: Optional[int],
    album_track_total: Optional[int],
    album_artist: Optional[str] = None,
    disc_number: Optional[int] = None,
    disc_total: Optional[int] = None,
    compilation: bool = False,
) -> None:
    audio = FLAC(str(path))
    audio['title'] = title
    if artists:
        audio['artist'] = artists
        audio['albumartist'] = album_artist or artists[0]
    if album:
        audio['album'] = album
    if track_number is not None:
        audio['tracknumber'] = str(track_number)
        if album_track_total is not None:
            audio['tracktotal'] = str(album_track_total)
    if disc_number is not None:
        audio['discnumber'] = str(disc_number)
        if disc_total is not None:
            audio['disctotal'] = str(disc_total)
    if year:
        audio['date'] = year
    if year and len(year) >= 4:
        audio['originaldate'] = year[:4]
    if genre:
        audio['genre'] = genre
    if compilation:
        audio['compilation'] = '1'
    if cover_bytes:
        picture = Picture()
        picture.data = cover_bytes
        picture.type = 3
        picture.mime = 'image/jpeg'
        audio.clear_pictures()
        audio.add_picture(picture)
    audio.save()


# BUG FIX 3: `cover_bytes` was entirely absent from _tag_ogg_vorbis, causing
# the positional argument passed by embed_metadata to land in `track_number`,
# shifting every subsequent positional arg by one slot and silently corrupting
# track/disc metadata.  Cover art embedding was also missing.
def _tag_ogg_vorbis(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    year: str,
    genre: str,
    cover_bytes: Optional[bytes],
    track_number: Optional[int],
    album_track_total: Optional[int],
    album_artist: Optional[str] = None,
    disc_number: Optional[int] = None,
    disc_total: Optional[int] = None,
    compilation: bool = False,
) -> None:
    audio = OggVorbis(str(path))
    _apply_vorbis_comments(
        audio,
        title,
        artists,
        album,
        year,
        genre,
        cover_bytes,
        track_number,
        album_track_total,
        album_artist,
        disc_number,
        disc_total,
        compilation,
    )
    audio.save()


# BUG FIX 4: Same missing `cover_bytes` parameter as _tag_ogg_vorbis above.
def _tag_opus(
    path: Path,
    title: str,
    artists: list[str],
    album: str,
    year: str,
    genre: str,
    cover_bytes: Optional[bytes],
    track_number: Optional[int],
    album_track_total: Optional[int],
    album_artist: Optional[str] = None,
    disc_number: Optional[int] = None,
    disc_total: Optional[int] = None,
    compilation: bool = False,
) -> None:
    audio = OggOpus(str(path))
    _apply_vorbis_comments(
        audio,
        title,
        artists,
        album,
        year,
        genre,
        cover_bytes,
        track_number,
        album_track_total,
        album_artist,
        disc_number,
        disc_total,
        compilation,
    )
    audio.save()


# BUG FIX 5: `cover_bytes` was missing from _apply_vorbis_comments, so OGG/Opus
# files never had cover art embedded even when cover data was available.
# Added METADATA_BLOCK_PICTURE embedding using the same base64 approach that
# Vorbis/Opus players expect per the spec.
def _apply_vorbis_comments(
    audio,
    title,
    artists,
    album,
    year,
    genre,
    cover_bytes: Optional[bytes],
    track_number: Optional[int],
    album_track_total: Optional[int],
    album_artist: Optional[str] = None,
    disc_number: Optional[int] = None,
    disc_total: Optional[int] = None,
    compilation: bool = False,
):
    import base64
    import struct

    audio['title'] = title
    if artists:
        audio['artist'] = artists
        audio['albumartist'] = album_artist or artists[0]
    if album:
        audio['album'] = album
    if track_number is not None:
        audio['TRACKNUMBER'] = str(track_number)
        if album_track_total is not None:
            audio['TRACKTOTAL'] = str(album_track_total)
    if disc_number is not None:
        audio['DISCNUMBER'] = str(disc_number)
        if disc_total is not None:
            audio['DISCTOTAL'] = str(disc_total)
    if year:
        audio['date'] = year
    if year and len(year) >= 4:
        audio['originaldate'] = year[:4]
    if genre:
        audio['genre'] = genre
    if compilation:
        audio['compilation'] = '1'
    if cover_bytes:
        # Encode cover art as METADATA_BLOCK_PICTURE per the Vorbis/Opus spec.
        mime = b'image/jpeg'
        desc = b''
        pic_type = 3  # Front cover
        data = cover_bytes
        block = struct.pack(
            '>IIII',
            pic_type,
            len(mime),
        ) + mime + struct.pack('>I', len(desc)) + desc + struct.pack(
            '>IIIIII',
            0, 0, 0, 0,  # width, height, color depth, color count
            len(data),
        ) + data
        # Re-pack with correct field count — build the full header properly:
        block = (
            struct.pack('>I', pic_type)
            + struct.pack('>I', len(mime)) + mime
            + struct.pack('>I', len(desc)) + desc
            + struct.pack('>IIII', 0, 0, 0, 0)
            + struct.pack('>I', len(data)) + data
        )
        audio['metadata_block_picture'] = [
            base64.b64encode(block).decode('ascii')
        ]


def embed_lyrics(path: Path, lyrics: 'lyrics_mod.Lyrics') -> None:
    if not path.exists() or not lyrics.has_any():
        return

    if lyrics.synced:
        sidecar = path.with_suffix('.lrc')
        try:
            sidecar.write_text(lyrics.synced, encoding='utf-8')
        except OSError:
            logger.opt(exception=True).warning(
                'Could not write LRC sidecar {}', sidecar
            )

    text = lyrics.plain or _strip_lrc_timestamps(lyrics.synced or '')
    if not text:
        return

    suffix = path.suffix.lower().lstrip('.')
    if suffix == 'mp3':
        audio = MP3(str(path), ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        tags: ID3 = audio.tags  # type: ignore[assignment]  # add_tags() guarantees non-None
        tags.delall('USLT')
        tags.add(USLT(encoding=3, lang='eng', desc='', text=text))
        audio.save(v2_version=3)
    elif suffix in {'m4a', 'mp4', 'aac'}:
        audio = MP4(str(path))
        audio['\xa9lyr'] = text
        audio.save()
    elif suffix == 'flac':
        audio = FLAC(str(path))
        audio['lyrics'] = text
        audio.save()
    elif suffix in {'ogg', 'oga'}:
        audio = OggVorbis(str(path))
        audio['lyrics'] = text
        audio.save()
    elif suffix == 'opus':
        audio = OggOpus(str(path))
        audio['lyrics'] = text
        audio.save()


def _strip_lrc_timestamps(synced: str) -> str:
    cleaned = re.sub(r'\[\d{1,2}:\d{2}(?:\.\d{1,3})?]', '', synced)
    return '\n'.join(
        line.strip() for line in cleaned.splitlines() if line.strip()
    )
