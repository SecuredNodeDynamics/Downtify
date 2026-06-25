package com.securednodedynamics.downtify;

import android.content.Context;
import android.os.Build;
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
import java.io.File;

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

    private static volatile boolean starting = false;
    private static volatile boolean crashed = false;

    @PluginMethod
    public void start(PluginCall call) {
        ensureStarted(getContext().getApplicationContext());
        call.resolve(info());
    }

    @PluginMethod
    public void getInfo(PluginCall call) {
        call.resolve(info());
    }

    private JSObject info() {
        JSObject ret = new JSObject();
        ret.put("baseUrl", BASE_URL);
        ret.put("port", PORT);
        ret.put("starting", starting);
        ret.put("crashed", crashed);
        return ret;
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
        final File musicDir = ctx.getExternalFilesDir("Music");
        final String downloadDir = (musicDir != null
            ? musicDir
            : new File(ctx.getFilesDir(), "downloads")).getAbsolutePath();
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
