package com.securednodedynamics.downtify;

import android.app.Activity;
import android.content.ContentResolver;
import android.content.Intent;
import android.content.UriPermission;
import android.net.Uri;
import android.util.Base64;
import androidx.activity.result.ActivityResult;
import androidx.documentfile.provider.DocumentFile;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.OutputStream;

@CapacitorPlugin(name = "FolderPicker")
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
}
