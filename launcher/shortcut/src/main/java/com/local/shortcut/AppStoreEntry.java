package com.local.shortcut;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;

/**
 * A tile that opens Xiaomi's app store and nothing else.
 *
 * com.xiaomi.mitv.appstore/.MainActivity is shipped enabled, but on this firmware it declares its
 * home activity only under the vendor's own {@code android.intent.category.APPSTORE_LAUNCHER}
 * category and not under LEANBACK_LAUNCHER, so every third-party launcher's app grid (including
 * CleanYourTV's) leaves it out. This activity is browseable on TV and forwards to that component.
 */
public class AppStoreEntry extends Activity {

    private static final String TARGET_PACKAGE = "com.xiaomi.mitv.appstore";
    private static final String TARGET_CLASS = "com.xiaomi.mitv.appstore.MainActivity";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent launch = new Intent(Intent.ACTION_MAIN);
        launch.setComponent(new ComponentName(TARGET_PACKAGE, TARGET_CLASS));
        launch.addCategory(Intent.CATEGORY_LAUNCHER);
        launch.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(launch);
        } catch (android.content.ActivityNotFoundException e) {
            // Fall back to whatever the store does expose (the market:// home route).
            Intent view = new Intent(Intent.ACTION_VIEW, android.net.Uri.parse("market://appstore.mitv.xiaomi.com/home"));
            view.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            try {
                startActivity(view);
            } catch (android.content.ActivityNotFoundException ignored) {
                // Nothing to open; leaving silently keeps the tile harmless.
            }
        }
        finish();
    }
}
