package com.securednodedynamics.downtify;

import android.os.Bundle;
import android.webkit.WebSettings;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ApkInstallerPlugin.class);
        registerPlugin(FolderPickerPlugin.class);
        registerPlugin(EmbeddedServerPlugin.class);
        super.onCreate(savedInstanceState);
        // The embedded backend is started on demand by the web layer (only in
        // on-device mode) via EmbeddedServer.start().
        allowMixedContent();
    }

    @Override
    public void onStart() {
        super.onStart();
        allowMixedContent();
    }

    private void allowMixedContent() {
        if (getBridge() == null || getBridge().getWebView() == null) {
            return;
        }
        getBridge()
            .getWebView()
            .getSettings()
            .setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
    }
}
