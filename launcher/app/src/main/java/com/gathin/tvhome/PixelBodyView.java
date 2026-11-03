package com.gathin.tvhome;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.View;

/**
 * The pixel figure that stands beside the habit panel's squares, drawn rather than shipped as art: a
 * 16 by 26 grid of squares, the same coin-slot face as the launcher's pixel clock, filled in for each
 * pose. Nothing here is a bitmap, so one class covers every shape and nothing has to be bundled.
 *
 * Two things decide what it looks like. The <em>pose</em> follows the clock: sitting on the ground
 * with the knees up and the belly rumbling from eleven at night until eight in the morning, standing
 * through the day, and holding a barbell at the belly between two and four in the afternoon. The
 * <em>shape</em> follows the newest weight recorded on the panel's weight page, five bodies from
 * round to lean (LEVELS below); a long break puts the weight back on because the level is read from
 * the weight itself and not remembered. The sitting pose is the one exception: it is drawn from a
 * single map of its own, so that its arms and knees stay where they can be read, and the width is
 * left to the other two.
 *
 * The lifting figure keeps the width the weight asks for, so unlike the sitting one it cannot be a
 * fixed map: the bar is drawn at full width and the hands are brought in to meet it from inside the
 * body's own outline, which is what leaves the room for a pair of plates at either end. The lift is
 * two frames swapped every half second - bar at the belly, bar overhead - which together read as one
 * repetition; the body stays on the same rows in both, so only the bar and the arms travel.
 */
public class PixelBodyView extends View {

    /** Which pose the clock asks for. */
    static final int POSE_STAND = 0;
    static final int POSE_RUN = 1;
    static final int POSE_FAINT = 2;

    /** Logical grid: every shape is drawn inside these bounds, whatever the view measures. */
    private static final int GRID_W = 16;
    private static final int GRID_H = 26;

    /** Half a second per frame: fast enough to be alive, slow enough to read as one lift. */
    private static final long FRAME_MS = 500L;

    /**
     * Shapes, round to lean: torso width, leg gap, face width. Width alone carries the weight now, and
     * the belly that used to poke out beside the sleeves is gone: it read as two loose yellow blocks
     * hanging off the arms, and the torso getting narrower says the same thing more plainly.
     */
    private static final float[][] LEVELS = {
            {10, 3, 8},   // round
            {9, 3, 8},
            {8, 2, 7},
            {7, 2, 6},
            {6, 1, 6},    // lean
    };

    /**
     * The pose for a run that has been left unfed: sitting on the ground, knees up and the arms round
     * them, mouth open, eyes gone to crosses, and the belly rumbling - the two blue marks beside it.
     * The stars have been lifted clear of the cap; sitting on the brim as they did, they read as a
     * pair of antlers. One map at the grid's own 16 by 26, and the letters are the colours below.
     */
    private static final String[] SITTING = {
            "................",
            "................",
            "................",
            "................",
            "....X...........",
            "...XXX.....X....",
            "....X.....XXX...",
            "...........X....",
            "....HHHHHH......",
            "...RRRRRRRR.....",
            "....SSSSSS......",
            "....SPSSPS......",
            "....SSMMSS......",
            "...OYYYYYYO.....",
            "...OTTTTTTO.....",
            "...OYYYYYYO.D...",
            "...OYYYYYYO..D..",
            "...OTTTTTTO.....",
            "...SEE..EES.....",
            "..GGGGGGGGGGGG..",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
    };

    private static final int SKIN = 0xFFF2C9A0;
    private static final int SWEAT = 0xFFD9A94E;
    private static final int STRIPE = 0xFFB5803A;
    private static final int HAT = 0xFFC98F3F;
    private static final int BRIM = 0xFFB57A2F;
    private static final int SHORT = 0xFF8A5A33;
    private static final int SHOE = 0xFF7A7468;
    private static final int SOCK = 0xFFF0EDE0;
    private static final int EYEW = 0xFFFFFFFF;
    private static final int PUP = 0xFF2C2C2A;
    private static final int MOUTH = 0xFF8A4A3A;
    private static final int STAR = 0xFFEF9F27;
    private static final int SWEATD = 0xFF9FCBE8;
    private static final int BAR = 0xFFB2B2BA;       // the chrome bar
    private static final int PLATE = 0xFF101216;     // the plates: near black, so they read heavy
    private static final int PLATE_RIM = 0xFF767C88; // the outer plate's edge, catching the light
    private static final int GROUND = 0x331E3A22;

    private final Paint paint = new Paint();
    private float unit = 6f;
    private int level;
    private int pose = POSE_STAND;
    private boolean frame;
    private boolean attached;

    private final Runnable flip = new Runnable() {
        @Override
        public void run() {
            frame = !frame;
            invalidate();
            schedule();
        }
    };

    public PixelBodyView(Context context, AttributeSet attrs) {
        super(context, attrs);
        // No smoothing: these are meant to be squares with hard edges, like everything else on the panel.
        paint.setAntiAlias(false);
    }

    /** Newest weight's body, 0 round to 4 lean. */
    void setLevel(int value) {
        int clamped = Math.max(0, Math.min(LEVELS.length - 1, value));
        if (clamped == level) return;
        level = clamped;
        invalidate();
    }

    /** POSE_STAND, POSE_RUN or POSE_FAINT. Starting to run starts the two frames swapping. */
    void setPose(int value) {
        if (value == pose) return;
        pose = value;
        frame = false;
        invalidate();
        schedule();
    }

    int getPose() {
        return pose;
    }

    @Override
    protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        unit = Math.min(w / (float) GRID_W, h / (float) GRID_H);
    }

    @Override
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        attached = true;
        schedule();
    }

    @Override
    protected void onDetachedFromWindow() {
        attached = false;
        removeCallbacks(flip);
        super.onDetachedFromWindow();
    }

    /** Only the lift moves, and only while this view is on the screen. */
    private void schedule() {
        removeCallbacks(flip);
        if (attached && pose == POSE_RUN && getVisibility() == VISIBLE) postDelayed(flip, FRAME_MS);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (unit <= 0) return;
        switch (pose) {
            case POSE_RUN:
                drawLifting(canvas, frame);
                break;
            case POSE_FAINT:
                drawFainted(canvas);
                break;
            default:
                drawStanding(canvas);
                break;
        }
    }

    /** One logical square. x, y, w and h are grid units, not pixels. */
    private void px(Canvas canvas, float x, float y, float w, float h, int colour) {
        if (w <= 0 || h <= 0) return;
        paint.setColor(colour);
        paint.setStyle(Paint.Style.FILL);
        float left = x * unit;
        float top = y * unit;
        canvas.drawRect(left, top, left + w * unit, top + h * unit, paint);
    }

    /** Where each part of this shape sits: centred on the grid's middle column whatever its width. */
    private float[] geom() {
        float[] l = LEVELS[level];
        float tw = l[0];
        float lg = l[1];
        float fw = l[2];
        return new float[]{
                tw, lg, fw,
                (GRID_W - tw) / 2f,         // torso left
                (GRID_W - fw) / 2f,         // head left
                (GRID_W - tw) / 2f - 2f,    // left sleeve, flush with the torso's side
                (GRID_W - tw) / 2f + tw,    // right sleeve
                (12f - lg) / 2f,            // left leg
                (12f - lg) / 2f + 2f + lg,  // right leg
        };
    }

    private void drawStanding(Canvas canvas) {
        float[] g = geom();
        // The order above: torso width, leg gap, face width, torso left, head left, left sleeve,
        // right sleeve, left leg, right leg - nine of them, and nothing past the last.
        float tw = g[0], fw = g[2], tx = g[3], fx = g[4], ax = g[5], bx = g[6], lx = g[7], rx = g[8];
        head(canvas, fx, 0f, fw);
        px(canvas, 7f, 7f, 2f, 1f, MOUTH);
        float cw = Math.max(2f, fw - 4f);
        px(canvas, 8f - cw / 2f, 8f, cw, 1f, SOCK);
        // Row by row, so the two brown bands run unbroken across the torso and both sleeves.
        for (int r = 0; r < 8; r++) {
            float y = 9f + r;
            int colour = (r == 2 || r == 5) ? STRIPE : SWEAT;      // the two brown bands: rows 11 and 14
            px(canvas, tx, y, tw, 1f, colour);
            // Sleeves start on the torso's top row, so the arms join at the shoulders and not the waist.
            px(canvas, ax, y, 2f, 1f, colour);
            px(canvas, bx, y, 2f, 1f, colour);
        }
        placket(canvas, tx, tw, 9f);
        px(canvas, ax, 16f, 2f, 2f, SKIN);
        px(canvas, bx, 16f, 2f, 2f, SKIN);
        px(canvas, tx, 18f, tw, 3f, SHORT);
        legs(canvas, lx, rx);
    }

    /**
     * The exercise pose, redrawn as a barbell lift. Two frames on one body: the bar held at the
     * belly, then pressed overhead - together they read as one repetition. The body keeps the width
     * the weight asks for, so unlike the sitting one this cannot be a fixed map; the bar is drawn at
     * full width and the hands are brought in to meet it from inside the body's own outline, which
     * is what leaves the room for a pair of plates at either end.
     */
    private void drawLifting(Canvas canvas, boolean overhead) {
        float[] g = geom();
        float tw = g[0], fw = g[2], tx = g[3], fx = g[4], lx = g[7], rx = g[8];
        if (overhead) {     // arms straight up beside the head, so the bar can be taken above it
            px(canvas, fx - 2f, 5f, 2f, 9f, SWEAT);
            px(canvas, fx + fw, 5f, 2f, 9f, SWEAT);
        }
        head(canvas, fx, 5f, fw);
        px(canvas, 7f, 12f, 2f, 1f, MOUTH);
        float cw = Math.max(2f, fw - 4f);
        px(canvas, 8f - cw / 2f, 13f, cw, 1f, SOCK);
        for (int r = 0; r < 6; r++) {   // torso, row by row so the brown bands run unbroken
            px(canvas, tx, 14f + r, tw, 1f, (r == 2 || r == 4) ? STRIPE : SWEAT);
        }
        px(canvas, tx, 20f, tw, 3f, SHORT);
        px(canvas, lx, 23f, 2f, 2f, SKIN);
        px(canvas, rx, 23f, 2f, 2f, SKIN);
        px(canvas, lx - 0.5f, 25f, 3f, 1f, SHOE);
        px(canvas, rx - 0.5f, 25f, 3f, 1f, SHOE);
        // The bar and its plates, drawn after the body so the bar lies in front of the belly. The
        // plates sit square on the bar's middle line: one row of plate above it for one below.
        float barTop = overhead ? 1f : 18f;
        px(canvas, 2f, barTop, 12f, 2f, BAR);
        px(canvas, 1f, barTop - 1f, 1f, 4f, PLATE);
        px(canvas, 14f, barTop - 1f, 1f, 4f, PLATE);
        px(canvas, 0f, barTop - 1f, 1f, 4f, PLATE_RIM);
        px(canvas, 15f, barTop - 1f, 1f, 4f, PLATE_RIM);
        if (overhead) {
            px(canvas, fx - 2f, 3f, 2f, 2f, SKIN);          // hands closing over the bar
            px(canvas, fx + fw, 3f, 2f, 2f, SKIN);
            px(canvas, 0f, 7f, 1f, 1f, SWEATD);
            px(canvas, 15f, 9f, 1f, 1f, SWEATD);
        } else {
            px(canvas, tx, 17f, 2f, 4f, SKIN);              // hands inside the body's own outline
            px(canvas, tx + tw - 2f, 17f, 2f, 4f, SKIN);
            px(canvas, 0f, 5f, 1f, 1f, SWEATD);
            px(canvas, 15f, 7f, 1f, 1f, SWEATD);
        }
    }

    /** Square by square out of the map: one letter, one square, and '.' is left to the panel's dark. */
    private void drawFainted(Canvas canvas) {
        for (int y = 0; y < SITTING.length; y++) {
            String row = SITTING[y];
            for (int x = 0; x < row.length(); x++) {
                int colour = colourOf(row.charAt(x));
                if (colour != 0) px(canvas, x, y, 1f, 1f, colour);
            }
        }
    }

    /** What each letter of the SITTING map stands for, or nothing at all for '.' and anything else. */
    private static int colourOf(char letter) {
        switch (letter) {
            case 'S': return SKIN;
            case 'Y': return SWEAT;
            case 'T': return STRIPE;
            case 'H': return HAT;
            case 'R': return BRIM;
            case 'O': return SHORT;
            case 'E': return SHOE;
            case 'K': return SOCK;
            case 'W': return EYEW;
            case 'P': return PUP;
            case 'M': return MOUTH;
            case 'X': return STAR;
            case 'D': return SWEATD;
            case 'G': return GROUND;
            default: return 0;
        }
    }

    private void head(Canvas canvas, float fx, float top, float fw) {
        px(canvas, fx, top, fw, 2f, HAT);
        px(canvas, fx - 1f, top + 2f, fw + 2f, 1f, BRIM);
        px(canvas, fx, top + 3f, fw, 4f, SKIN);
        float ew = fw >= 8f ? 3f : 2f;
        px(canvas, fx + 0.5f, top + 4f, ew, 2f, EYEW);
        px(canvas, fx + fw - 0.5f - ew, top + 4f, ew, 2f, EYEW);
        px(canvas, fx + 1.5f, top + 5f, 1f, 1f, PUP);
        px(canvas, fx + fw - 2.5f, top + 5f, 1f, 1f, PUP);
    }

    private void legs(Canvas canvas, float lx, float rx) {
        px(canvas, lx, 21f, 2f, 3f, SKIN);
        px(canvas, rx, 21f, 2f, 3f, SKIN);
        px(canvas, lx, 24f, 2f, 1f, SOCK);
        px(canvas, rx, 24f, 2f, 1f, SOCK);
        px(canvas, lx - 0.5f, 25f, 3f, 1f, SHOE);
        px(canvas, rx - 0.5f, 25f, 3f, 1f, SHOE);
    }

    /** The polo shirt's white placket: from the collar down to the end of the first yellow band. */
    private void placket(Canvas canvas, float tx, float tw, float top) {
        px(canvas, tx + tw / 2f - 0.5f, top, 1f, 2f, EYEW);
    }

}
