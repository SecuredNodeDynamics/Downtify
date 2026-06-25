package com.securednodedynamics.downtify;

import android.Manifest;
import android.app.Activity;
import android.content.ContentResolver;
import android.content.Intent;
import android.content.UriPermission;
import android.content.pm.PackageManager;
import android.media.MediaScannerConnection;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.DocumentsContract;
import android.provider.Settings;
import android.util.Base64;
import androidx.activity.result.ActivityResult;
import androidx.core.content.ContextCompat;
import androidx.documentfile.provider.DocumentFile;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.io.File;
import java.io.OutputStream;

@CapacitorPlugin(
    name = "FolderPicker",
    permissions = {
        @Permission(
            alias = "storage",
            strings = {
                Manifest.permission.READ_EXTERNAL_STORAGE,
                Manifest.permission.WRITE_EXTERNAL_STORAGE,
            }
        ),
    }
)
public class FolderPickerPlugin extends Plugin {

    @PluginMethod
    public void pickFolder(PluginCall call) {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(
            Intent.FLAG_GRANT_READ_URI_PERMISSION |
            Intent.FLAG_GRANT_WRITE_URI_PERMISSION |
            Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
        );
        startActivityForResult(call, intent, "folderPicked");
    }

    @ActivityCallback
    private void folderPicked(PluginCall call, ActivityResult result) {
        if (call == null) {
            return;
        }
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null) {
            call.reject("cancelled");
            return;
        }
        Uri treeUri = result.getData().getData();
        if (treeUri == null) {
            call.reject("no-uri");
            return;
        }
        int flags =
            Intent.FLAG_GRANT_READ_URI_PERMISSION |
            Intent.FLAG_GRANT_WRITE_URI_PERMISSION;
        try {
            getContext().getContentResolver().takePersistableUriPermission(treeUri, flags);
        } catch (Exception exc) {
            // Permission may already be held or not be persistable; continue.
        }
        DocumentFile tree = DocumentFile.fromTreeUri(getContext(), treeUri);
        String name = tree != null ? tree.getName() : null;
        JSObject ret = new JSObject();
        ret.put("uri", treeUri.toString());
        ret.put("name", name != null ? name : "");
        // A real filesystem path lets the embedded Python backend read/write the
        // folder directly so the Library and Player tabs can see the media.
        String path = pathFromTreeUri(treeUri);
        ret.put("path", path != null ? path : "");
        call.resolve(ret);
    }

    @PluginMethod
    public void checkPermission(PluginCall call) {
        String uriStr = call.getString("uri");
        boolean granted = false;
        if (uriStr != null && !uriStr.isEmpty()) {
            Uri uri = Uri.parse(uriStr);
            for (UriPermission permission : getContext()
                .getContentResolver()
                .getPersistedUriPermissions()) {
                if (permission.getUri().equals(uri) && permission.isWritePermission()) {
                    granted = true;
                    break;
                }
            }
        }
        JSObject ret = new JSObject();
        ret.put("granted", granted);
        call.resolve(ret);
    }

    /**
     * Returns the default shared "music library" download folder
     * (.../Music/Downtify) so downloads land where the device's own music apps
     * can see them.
     */
    @PluginMethod
    public void getDefaultMusicDir(PluginCall call) {
        File music = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_MUSIC
        );
        File dir = new File(music, "Downtify");
        JSObject ret = new JSObject();
        ret.put("path", dir.getAbsolutePath());
        call.resolve(ret);
    }

    /** Whether the app can read/write shared storage by absolute path. */
    @PluginMethod
    public void hasAllFilesAccess(PluginCall call) {
        JSObject ret = new JSObject();
        ret.put("granted", hasAllFilesAccessInternal());
        call.resolve(ret);
    }

    /**
     * Requests broad storage access so the embedded backend can read/write the
     * user's chosen folder. On Android 11+ this opens the "All files access"
     * settings screen; on older versions it requests the legacy storage runtime
     * permission.
     */
    @PluginMethod
    public void requestAllFilesAccess(PluginCall call) {
        if (hasAllFilesAccessInternal()) {
            JSObject ret = new JSObject();
            ret.put("granted", true);
            call.resolve(ret);
            return;
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                Intent intent = new Intent(
                    Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION
                );
                intent.setData(Uri.parse("package:" + getContext().getPackageName()));
                startActivityForResult(call, intent, "allFilesAccessResult");
                return;
            } catch (Exception exc) {
                try {
                    Intent intent = new Intent(
                        Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION
                    );
                    startActivityForResult(call, intent, "allFilesAccessResult");
                    return;
                } catch (Exception ignored) {
                    // Fall through to resolving with the current state.
                }
            }
            JSObject ret = new JSObject();
            ret.put("granted", hasAllFilesAccessInternal());
            call.resolve(ret);
            return;
        }
        requestPermissionForAlias("storage", call, "storagePermsCallback");
    }

    @ActivityCallback
    private void allFilesAccessResult(PluginCall call, ActivityResult result) {
        if (call == null) {
            return;
        }
        JSObject ret = new JSObject();
        ret.put("granted", hasAllFilesAccessInternal());
        call.resolve(ret);
    }

    @PermissionCallback
    private void storagePermsCallback(PluginCall call) {
        JSObject ret = new JSObject();
        ret.put("granted", hasAllFilesAccessInternal());
        call.resolve(ret);
    }

    /**
     * Asks the system MediaScanner to index a freshly written file so it shows
     * up in the device's music library / other media apps.
     */
    @PluginMethod
    public void scanMedia(PluginCall call) {
        String path = call.getString("path");
        if (path == null || path.isEmpty()) {
            call.reject("no-path");
            return;
        }
        try {
            MediaScannerConnection.scanFile(
                getContext(),
                new String[] { path },
                null,
                null
            );
        } catch (Exception exc) {
            // Scanning is best-effort; the file is still on disk regardless.
        }
        call.resolve();
    }

    @PluginMethod
    public void writeFile(PluginCall call) {
        String uriStr = call.getString("uri");
        String relativePath = call.getString("path");
        String data = call.getString("data");
        String mimeType = call.getString("mimeType", "application/octet-stream");
        if (uriStr == null || relativePath == null || data == null) {
            call.reject("missing-args");
            return;
        }

        getBridge()
            .execute(() -> {
                try {
                    Uri treeUri = Uri.parse(uriStr);
                    DocumentFile dir = DocumentFile.fromTreeUri(getContext(), treeUri);
                    if (dir == null || !dir.canWrite()) {
                        call.reject("invalid-folder");
                        return;
                    }

                    String[] segments = relativePath.split("/");
                    String fileName = segments[segments.length - 1];
                    if (fileName.isEmpty()) {
                        call.reject("no-filename");
                        return;
                    }

                    for (int i = 0; i < segments.length - 1; i++) {
                        String seg = segments[i];
                        if (seg.isEmpty()) {
                            continue;
                        }
                        DocumentFile child = dir.findFile(seg);
                        if (child == null || !child.isDirectory()) {
                            child = dir.createDirectory(seg);
                        }
                        if (child == null) {
                            call.reject("mkdir-failed");
                            return;
                        }
                        dir = child;
                    }

                    DocumentFile existing = dir.findFile(fileName);
                    if (existing != null) {
                        existing.delete();
                    }
                    DocumentFile file = dir.createFile(mimeType, fileName);
                    if (file == null) {
                        call.reject("create-failed");
                        return;
                    }

                    byte[] bytes = Base64.decode(data, Base64.DEFAULT);
                    ContentResolver resolver = getContext().getContentResolver();
                    try (OutputStream out = resolver.openOutputStream(file.getUri())) {
                        if (out == null) {
                            call.reject("open-failed");
                            return;
                        }
                        out.write(bytes);
                    }

                    JSObject ret = new JSObject();
                    ret.put("uri", file.getUri().toString());
                    call.resolve(ret);
                } catch (Exception exc) {
                    call.reject(
                        exc.getMessage() != null ? exc.getMessage() : "write-failed",
                        exc
                    );
                }
            });
    }

    private boolean hasAllFilesAccessInternal() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            return Environment.isExternalStorageManager();
        }
        return (
            ContextCompat.checkSelfPermission(
                getContext(),
                Manifest.permission.WRITE_EXTERNAL_STORAGE
            ) ==
            PackageManager.PERMISSION_GRANTED
        );
    }

    /**
     * Best-effort conversion of a SAF tree URI into an absolute filesystem path
     * on primary/secondary external storage. Returns {@code null} when the URI
     * does not map to a plain file path (e.g. cloud providers).
     */
    private String pathFromTreeUri(Uri treeUri) {
        try {
            String docId = DocumentsContract.getTreeDocumentId(treeUri);
            if (docId == null) {
                return null;
            }
            String[] split = docId.split(":", 2);
            String volume = split[0];
            String relative = split.length > 1 ? split[1] : "";
            if ("primary".equalsIgnoreCase(volume)) {
                File base = Environment.getExternalStorageDirectory();
                return relative.isEmpty()
                    ? base.getAbsolutePath()
                    : new File(base, relative).getAbsolutePath();
            }
            File mounted = new File("/storage/" + volume);
            if (mounted.exists()) {
                return relative.isEmpty()
                    ? mounted.getAbsolutePath()
                    : new File(mounted, relative).getAbsolutePath();
            }
        } catch (Exception exc) {
            // Not a file-backed tree; caller falls back to SAF writes.
        }
        return null;
    }
}
