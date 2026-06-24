package com.securednodedynamics.downtify;

import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import androidx.core.content.FileProvider;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

@CapacitorPlugin(name = "ApkInstaller")
public class ApkInstallerPlugin extends Plugin {

    @PluginMethod
    public void downloadAndInstall(PluginCall call) {
        String url = call.getString("url");
        if (url == null || url.isEmpty()) {
            call.reject("Missing APK download URL");
            return;
        }

        getBridge()
            .execute(() -> {
                try {
                    ensureInstallPermission();
                    File apkFile = downloadApk(url);
                    installApk(apkFile);
                    call.resolve();
                } catch (Exception exc) {
                    call.reject(exc.getMessage() != null ? exc.getMessage() : "APK update failed", exc);
                }
            });
    }

    private void ensureInstallPermission() throws Exception {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }
        if (getContext().getPackageManager().canRequestPackageInstalls()) {
            return;
        }
        Intent intent = new Intent(
            Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
            Uri.parse("package:" + getContext().getPackageName())
        );
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(intent);
        throw new Exception(
            "Allow installs from this app in Android settings, then try again."
        );
    }

    private File downloadApk(String urlString) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestProperty("User-Agent", "Downtify-Android");
        connection.setInstanceFollowRedirects(true);
        connection.connect();

        int status = connection.getResponseCode();
        if (status >= 400) {
            throw new Exception("Download failed with HTTP " + status);
        }

        File apkFile = new File(getContext().getCacheDir(), "downtify-update.apk");
        try (
            InputStream input = connection.getInputStream();
            FileOutputStream output = new FileOutputStream(apkFile)
        ) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
            }
        }
        return apkFile;
    }

    private void installApk(File apkFile) {
        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        Uri apkUri;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            apkUri = FileProvider.getUriForFile(
                getContext(),
                getContext().getPackageName() + ".fileprovider",
                apkFile
            );
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } else {
            apkUri = Uri.fromFile(apkFile);
        }
        intent.setDataAndType(apkUri, "application/vnd.android.package-archive");
        getContext().startActivity(intent);
    }
}
