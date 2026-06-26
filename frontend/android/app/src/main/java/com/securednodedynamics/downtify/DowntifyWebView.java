package com.securednodedynamics.downtify;

import android.content.Context;
import android.util.AttributeSet;
import android.view.View;
import com.getcapacitor.CapacitorWebView;

/**
 * Android WebView pauses HTML5 media when the window is hidden (app minimized or
 * screen off). Pretend the view stays visible so audio keeps playing while a
 * media-session foreground service holds the process awake.
 */
public class DowntifyWebView extends CapacitorWebView {

    public DowntifyWebView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    @Override
    public void onWindowVisibilityChanged(int visibility) {
        super.onWindowVisibilityChanged(View.VISIBLE);
    }
}
