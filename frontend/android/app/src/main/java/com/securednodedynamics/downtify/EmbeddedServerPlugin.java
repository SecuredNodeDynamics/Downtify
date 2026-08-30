package com.securednodedynamics.downtify;

import android.content.Context;
import android.os.Build;
import android.os.Environment;
import android.util.Log;
import com.chaquo.python.Kwarg;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

/**
 * Runs the full Downtify FastAPI backend in-process via Chaquopy so the APK
 * works with no external server (serverless mode). The WebView talks to it
 * over http://127.0.0.1:PORT exactly like a remote server.
 */
@CapacitorPlugin(name = "EmbeddedServer")
public class EmbeddedServerPlugin extends Plugin {

    private static final String TAG = "EmbeddedServer";
    private static final int PORT = 8765;
    private static final String BASE_URL = "http://127.0.0.1:" + PORT;
    private static final String PREFS = "downtify_embedded";
    private static final String PREF_DOWNLOAD_DIR = "download_dir";

    private static volatile boolean starting = false;
    private static volatile boolean crashed = false;

    @PluginMethod
    public void start(PluginCall call) {
        JSObject ret = new JSObject();
        ret.put("baseUrl", BASE_URL);
        ret.put("port", PORT);
        ret.put("starting", true);
        ret.put("crashed", crashed);
        ret.put("downloadDir", "");
        call.resolve(ret);
        ensureStarted(getContext().getApplicationContext());
    }

    @PluginMethod
    public void getInfo(PluginCall call) {
        call.resolve(info());
    }

    @PluginMethod
    public void setDownloadDir(PluginCall call) {
        String path = call.getString("path", "");
        if (path == null) path = "";
        path = path.trim();
        Context ctx = getContext().getApplicationContext();
        if (!path.isEmpty() && new File(path).isDirectory()) {
            rememberDownloadDir(ctx, path);
        }
        call.resolve(info());
    }

    private JSObject info() {
        Context ctx = getContext().getApplicationContext();
        JSObject ret = new JSObject();
        ret.put("baseUrl", BASE_URL);
        ret.put("port", PORT);
        ret.put("starting", starting);
        ret.put("crashed", crashed);
        ret.put("downloadDir", activeDownloadDir(ctx));
        return ret;
    }

    /**
     * Folder Android Auto and the WebView should treat as the library root:
     * Python's last applied DOWNLOAD_DIR, then a remembered picker path, then
     * the default Music/Downtify (or app-private) directory.
     */
    static String activeDownloadDir(Context ctx) {
        String fromMarker = readMarkerDir(ctx);
        if (isExistingDir(fromMarker)) return fromMarker;
        String stored = ctx
            .getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(PREF_DOWNLOAD_DIR, "");
        if (isExistingDir(stored)) return stored;
        return defaultDownloadDir(ctx);
    }

    static void rememberDownloadDir(Context ctx, String path) {
        if (!isExistingDir(path)) return;
        ctx
            .getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(PREF_DOWNLOAD_DIR, path)
            .apply();
    }

    private static String readMarkerDir(Context ctx) {
        File marker = new File(
            new File(ctx.getFilesDir(), "downtify-data"),
            "active_download_dir.txt"
        );
        if (!marker.isFile()) return "";
        try (
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(
                    new FileInputStream(marker),
                    StandardCharsets.UTF_8
                )
            )
        ) {
            String line = reader.readLine();
            return line == null ? "" : line.trim();
        } catch (Exception ignored) {
            return "";
        }
    }

    private static boolean isExistingDir(String path) {
        if (path == null || path.isEmpty()) return false;
        if (
            !(path.startsWith("/storage/") ||
                path.startsWith("/sdcard") ||
                path.startsWith("/data/"))
        ) {
            return false;
        }
        try {
            File file = new File(path);
            return file.isDirectory();
        } catch (Exception ignored) {
            return false;
        }
    }

    /**
     * The folder the embedded backend writes downloads to by default. When the
     * app holds broad storage access it uses the device's shared Music library
     * (.../Music/Downtify) so other apps can see the files; otherwise it falls
     * back to app-private external storage, which needs no permission.
     */
    static String defaultDownloadDir(Context ctx) {
        boolean canUseShared;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            canUseShared = Environment.isExternalStorageManager();
        } else {
            canUseShared = Environment.MEDIA_MOUNTED.equals(
                Environment.getExternalStorageState()
            );
        }
        if (canUseShared) {
            File music = Environment.getExternalStoragePublicDirectory(
                Environment.DIRECTORY_MUSIC
            );
            File shared = new File(music, "Downtify");
            if (shared.mkdirs() || shared.isDirectory()) {
                return shared.getAbsolutePath();
            }
        }
        File musicDir = ctx.getExternalFilesDir("Music");
        return (musicDir != null
            ? musicDir
            : new File(ctx.getFilesDir(), "downloads")).getAbsolutePath();
    }

    /**
     * Idempotently boots the embedded server on a background thread. Safe to
     * call from {@link MainActivity#onCreate} and from the JS bridge.
     */
    static synchronized void ensureStarted(Context context) {
        if (starting) {
            return;
        }
        starting = true;
        crashed = false;

        final Context ctx = context.getApplicationContext();
        final String dataDir = new File(ctx.getFilesDir(), "downtify-data")
            .getAbsolutePath();
        final String downloadDir = defaultDownloadDir(ctx);
        final String nativeLibDir = ctx.getApplicationInfo().nativeLibraryDir;

        Thread thread = new Thread(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(ctx));
                }
                Python py = Python.getInstance();
                PyObject mobile = py.getModule("downtify.mobile");
                mobile.callAttr(
                    "run_server",
                    new Kwarg("data_dir", dataDir),
                    new Kwarg("download_dir", downloadDir),
                    new Kwarg("native_lib_dir", nativeLibDir),
                    new Kwarg("port", PORT),
                    new Kwarg("host", "127.0.0.1")
                );
            } catch (Throwable t) {
                crashed = true;
                starting = false;
                Log.e(TAG, "Embedded Downtify server stopped", t);
            }
        }, "downtify-embedded-server");
        thread.setDaemon(true);
        thread.start();
    }
}
