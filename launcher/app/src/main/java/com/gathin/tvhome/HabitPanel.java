package com.gathin.tvhome;

import android.content.Context;
import android.graphics.Rect;
import android.graphics.drawable.GradientDrawable;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

/**
 * The habit calendar: one pixel square per day, seven to a row, Monday first, and not a word of text
 * anywhere on it. Two pages, held by the panel's cursor:
 *
 *  - the month: the calendar month, padded out to whole weeks, so five rows and six in the long ones.
 *    Right turns to the weight page. Left is no direction here but the way the day is kept: two
 *    presses of it, close together, tick today, and one press alone does nothing at all;
 *  - the weight: today's weight, the curve of the run so far, and how far there is still to go. One
 *    press of left and the calendar is back.
 *
 * A square is green for a day kept and dark grey for a day missed, whether that day has been or not.
 * Today is given no colour of its own: it is a day like the others, missed until it is ticked, so a
 * week reads the same whoever looks at it. The cursor says which day is today by growing that square
 * a little and nothing else, and OK keeps the day or takes the tick back.
 *
 * Beside the squares stands a pixel figure. Its pose follows the clock: sitting and hungry from eleven
 * at night until eight in the morning, standing through the day, and lifting a barbell between two
 * and four in the afternoon. Its shape follows the weight:
 * five bodies spread over habit_weight_steps, read from the newest weight typed in and from nothing
 * else, so it thins down as the weight comes off and fills back out again if the run stops. There is
 * no remembered shape to lose, and nothing to reset after a break.
 *
 * The panel is a child of the root frame and not of the shelf, so it floats over the top of the first
 * row of tiles: the shelf, the grid and the dock stay exactly where they were. The left column keeps
 * six rows of room whatever the month needs, so nothing here can move the panel either.
 */
final class HabitPanel {

    private static final int COLUMNS = 7;

    private static final int MODE_GRID = 0;
    private static final int MODE_WEIGHT = 1;

    /** Kept, missed, not yet here, and before the run began. */
    private static final int DONE = 0xFF97C459;
    private static final int MISSED = 0xFF3A3A40;
    private static final int FUTURE = 0xFF26262C;
    private static final int BEFORE = 0xFF1C1E23;
    private static final int PAD = 0x00000000;

    /** Today's square under the cursor: bigger, not brighter. */
    private static final float FOCUS_SCALE = 1.18f;

    /** Nobody weighs this much, and nobody weighs nothing: they keep a mistyped key from running away. */
    private static final float MIN_KG = 25f;
    private static final float MAX_KG = 300f;

    /** How long the first of the two left presses stays waiting for its partner. */
    private static final long DOUBLE_LEFT_MS = 800L;

    /** The clock's three turns: hungry from eleven at night to eight in the morning, a lift from two
     *  until four in the afternoon, and standing at every hour between. */
    private static final int HUNGRY_FROM = 23;
    private static final int HUNGRY_TO = 8;
    private static final int RUN_FROM = 14;
    private static final int RUN_TO = 16;

    private final Context context;
    private final View panel;
    private final LinearLayout grid;
    private final View weightPage;
    private final WeightChartView chart;
    private final PixelBodyView body;
    private final TextView streakText;
    private final TextView levelText;
    private final TextView startText;
    private final TextView nowText;
    private final TextView goalText;
    private final TextView editHint;
    private final TextView saveHint;
    private final View input;
    private final TextView draftText;
    /** A grid of squares with the gap about half a square, which is what the drawing asked for. */
    private final int cell;
    private final int gap;
    private final float radius;
    /** Every square now on the panel, in reading order, so the cursor can be taken off them. */
    private final List<View> cells = new ArrayList<>();
    private boolean on;
    private boolean weightOn;
    private int mode = MODE_GRID;
    private LocalDate start;
    private View todayCell;
    private boolean focused;
    /** The five shapes' boundaries, heaviest first: 80, 77, 74, 71, 68, 65 by default. */
    private float[] steps = {80f, 77f, 74f, 71f, 68f, 65f};
    private float editStep = 0.1f;
    /** Today's weight as it is being typed, before OK makes it the day's record. Float until then. */
    private Float draft;
    /** When the first of the two left presses landed, or zero when none is waiting. */
    private long lastLeftAt;
    /**
     * Whether the row the cursor is on leaves the panel's patch of screen clear: true for the dock's
     * row, which is parked along the bottom and never rides up behind the panel, false for any row
     * below it. Null before the first move says anything, and then the geometry has to answer alone.
     */
    private Boolean rowClear;
    /** Whether the weight box is open for typing, which takes an OK to enter and an OK to close. */
    private boolean editing;

    HabitPanel(Context context, View panelView) {
        this.context = context.getApplicationContext();
        this.panel = panelView;
        this.grid = panelView.findViewById(R.id.habitGrid);
        this.weightPage = panelView.findViewById(R.id.weightPage);
        this.chart = panelView.findViewById(R.id.weightChart);
        this.body = panelView.findViewById(R.id.habitBody);
        this.streakText = panelView.findViewById(R.id.habitStreak);
        this.levelText = panelView.findViewById(R.id.weightLevel);
        this.startText = panelView.findViewById(R.id.weightStart);
        this.nowText = panelView.findViewById(R.id.weightNow);
        this.goalText = panelView.findViewById(R.id.weightGoal);
        this.editHint = panelView.findViewById(R.id.weightEditHint);
        this.saveHint = panelView.findViewById(R.id.weightSaveHint);
        this.input = panelView.findViewById(R.id.weightInput);
        this.draftText = panelView.findViewById(R.id.weightDraft);
        float density = context.getResources().getDisplayMetrics().density;
        // Six rows of these have to stand between the clock and the dock without crowding either, so the
        // square is 22dp (the gap still half a square, as the drawing asked) and not the 25 first tried.
        this.cell = Math.round(22 * density);
        this.gap = Math.round(11 * density);
        this.radius = 6 * density;
    }

    /**
     * config.xml habit_calendar: false leaves the panel gone and nothing is read. The weight page comes
     * up alongside it when habit_weight_page is on; "steps" are the six weights that bound the five
     * bodies, and "editStep" is how much up and down move today's weight by, in kg.
     */
    void setup(boolean enabled, LocalDate startDay, boolean weightPageOn, float[] bodySteps, float stepKg) {
        on = enabled;
        start = startDay == null ? LocalDate.now() : startDay;
        weightOn = weightPageOn;
        if (bodySteps != null && bodySteps.length >= 2) steps = bodySteps;
        if (stepKg > 0f) editStep = stepKg;
        if (!on) {
            panel.setVisibility(View.GONE);
            return;
        }
        panel.setVisibility(View.VISIBLE);
        panel.setOnClickListener(v -> tick());
        panel.setOnFocusChangeListener((v, has) -> {
            focused = has;
            paintFocus();
        });
        panel.setOnKeyListener(this::onKey);
        input.setOnKeyListener(this::onWeightKey);
        input.setOnFocusChangeListener((v, has) -> {
            setEditing(false);
            input.setBackgroundResource(has ? R.drawable.habit_weight_input_bg_focused
                    : R.drawable.habit_weight_input_bg);
        });
        setEditing(false);
        draw();
    }

    boolean isOn() {
        return on;
    }

    /** On the minute and on every return to Home: the day may have rolled over while away. */
    void refresh() {
        if (on) draw();
    }

    boolean requestFocus() {
        return panel.requestFocus();
    }

    /**
     * The cursor has landed on a tile, and which row decides the panel's fate there and then, before
     * the list has had time to move. The dock's row is parked along the bottom and leaves the panel's
     * patch of screen clear; every row below it is only reached by scrolling, and the tiles ride up
     * behind the panel as they go. Waiting for the scroll to arrive and measuring it afterwards left
     * the panel hanging on for as long as the list took to travel, a beat behind the cursor that had
     * already left the dock, so the row is asked instead and the geometry only stands in for it.
     */
    void onRowFocused(boolean clear) {
        if (!on) return;
        rowClear = clear;
        fade(!clear);
    }

    /**
     * Called for every move of the cursor (MainActivity watches the whole window) and for every
     * scroll of the list under it. The test is not where the cursor is but whether any tile has been
     * scrolled up into the panel's patch of screen: the dock and the rows above it leave the panel
     * standing whole, and from the row below the dock on, where the tiles ride up behind it and cut
     * it in half, it fades out instead of being worn as a window onto the apps. It stays focusable
     * either way, so up from beneath it still finds it.
     */
    void onFocusMoved(View target, View apps) {
        if (!on) return;
        if (target == null || within(target, panel)) {
            fade(false);   // the panel's own cursor, or nothing at all: it stays on screen
            return;
        }
        // Away from the tiles altogether - the shelf, the clock - no row speaks for it, and only the
        // geometry is left to say whether anything is standing behind the panel.
        if (!within(target, apps)) rowClear = null;
        fade(rowClear != null ? !rowClear : overlapped(apps));
    }

    /** True when any tile has ridden up into the panel's patch of screen. Only good once the list has
     *  stopped, which is why the row is asked first on a move and this is left to hold the answer
     *  steady while the list travels. */
    private boolean overlapped(View apps) {
        if (!(apps instanceof android.view.ViewGroup)) return false;
        android.view.ViewGroup rows = (android.view.ViewGroup) apps;
        Rect mine = where(panel);
        for (int i = 0; i < rows.getChildCount(); i++) {
            View tile = rows.getChildAt(i);
            if (tile.getVisibility() != View.VISIBLE || tile.getWidth() == 0) continue;
            // Anything scrolled in behind the panel counts, half a tile included; a tile that has
            // itself been faded out does not.
            if (tile.getAlpha() > 0.05f && Rect.intersects(where(tile), mine)) return true;
        }
        return false;
    }

    /** Out at once, back gently: a panel that lags behind the cursor reads as a fault, one that
     *  returns as the list settles reads as the list settling. */
    private void fade(boolean covered) {
        float to = covered ? 0f : 1f;
        if (panel.getAlpha() == to) return;
        panel.animate().cancel();
        panel.animate().alpha(to).setDuration(covered ? 110L : 160L).start();
    }

    /** Where a view sits on the screen, in a rect of its own, for the overlap test above. */
    private static Rect where(View view) {
        int[] at = new int[2];
        view.getLocationOnScreen(at);
        return new Rect(at[0], at[1], at[0] + view.getWidth(), at[1] + view.getHeight());
    }

    /** True when the view is the given parent or anything inside it, for telling the panel's own
     *  children apart from the tiles that ride up behind it. */
    private static boolean within(View view, View parent) {
        for (View v = view; v != null; v = v.getParent() instanceof View ? (View) v.getParent() : null) {
            if (v == parent) return true;
        }
        return false;
    }

    private boolean onKey(View view, int keyCode, KeyEvent event) {
        if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
        if (keyCode == KeyEvent.KEYCODE_DPAD_LEFT) {
            if (event.getRepeatCount() > 0) return true;
            if (mode == MODE_WEIGHT) {
                // One press on the weight page and you are back on the calendar.
                setMode(MODE_GRID);
                return true;
            }
            // On the calendar, left is a gesture and not a direction: two presses inside the window
            // keep the day, and one on its own does nothing, so leaning on the pad cannot tick it.
            long now = SystemClock.uptimeMillis();
            if (now - lastLeftAt <= DOUBLE_LEFT_MS) {
                lastLeftAt = 0L;
                tick();
            } else {
                lastLeftAt = now;
            }
            return true;
        }
        if (keyCode == KeyEvent.KEYCODE_DPAD_RIGHT) {
            if (event.getRepeatCount() > 0) return true;
            if (mode == MODE_GRID) setMode(MODE_WEIGHT);
            return true;   // the weight page is the last one: nothing sits to its right
        }
        if (keyCode == KeyEvent.KEYCODE_DPAD_CENTER || keyCode == KeyEvent.KEYCODE_ENTER) {
            if (event.getRepeatCount() > 0) return true;
            if (mode == MODE_WEIGHT) {
                // Straight from the panel, OK opens the box rather than only pointing at it.
                if (input.requestFocus()) setEditing(true);
            } else {
                tick();
            }
            return true;
        }
        return false;   // up and down move the cursor as usual
    }

    /**
     * The weight box holds the cursor and nothing more. Down only selects it; nothing moves until OK
     * opens it for editing, and OK again closes it and records what was typed. Up and down are live
     * only in between, so reaching past the box on the way down cannot quietly shift the weight.
     */
    private boolean onWeightKey(View view, int keyCode, KeyEvent event) {
        if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
        if (keyCode == KeyEvent.KEYCODE_DPAD_CENTER || keyCode == KeyEvent.KEYCODE_ENTER) {
            if (event.getRepeatCount() > 0) return true;
            if (editing) {
                commit();
                setEditing(false);
            } else {
                setEditing(true);
            }
            return true;
        }
        if (editing) {
            if (keyCode == KeyEvent.KEYCODE_DPAD_UP) {
                nudge(editStep);
                return true;
            }
            if (keyCode == KeyEvent.KEYCODE_DPAD_DOWN) {
                nudge(-editStep);
                return true;
            }
        }
        // Not editing: up and down go on their way, to the panel above or the apps below.
        if (keyCode == KeyEvent.KEYCODE_DPAD_LEFT) {
            if (event.getRepeatCount() > 0) return true;
            panel.requestFocus();
            setMode(MODE_GRID);
            return true;
        }
        if (keyCode == KeyEvent.KEYCODE_DPAD_RIGHT) {
            return true;   // the weight page is the last one: nothing sits to its right
        }
        return false;
    }

    /** One page or the other, and never by accident: only the keys above ask for a change. */
    private void setMode(int next) {
        if (!weightOn && next == MODE_WEIGHT) return;
        if (mode == next) return;
        mode = next;
        lastLeftAt = 0L;
        setEditing(false);
        if (mode == MODE_WEIGHT) draft = null;   // take the day's weight afresh on arrival
        draw();
    }

    /**
     * Editing is a state you have to ask for. Closed, the box shows the weight and asks for OK; open,
     * the edge lights up, up and down take the weight by habit_weight_step, and OK writes it down.
     */
    private void setEditing(boolean value) {
        editing = value;
        input.setBackgroundResource(value ? R.drawable.habit_weight_input_bg_editing
                : R.drawable.habit_weight_input_bg_focused);
        if (value) {
            editHint.setText(context.getString(R.string.habit_weight_edit, String.valueOf(editStep)));
            saveHint.setText(R.string.habit_weight_save);
            saveHint.setVisibility(View.VISIBLE);
        } else {
            editHint.setText(R.string.habit_weight_prompt);
            saveHint.setVisibility(View.GONE);
        }
    }

    /** OK: keep today, or take the tick back. */
    private void tick() {
        HabitCalendar.toggle(context, LocalDate.now());
        draw();
    }

    private void nudge(float by) {
        if (draft == null) return;
        draft = clamp(Math.round((draft + by) * 100f) / 100f);
        draftText.setText(kg2(draft));
    }

    /** OK in the weight box: today's weight becomes what the run is measured against. */
    private void commit() {
        if (draft == null) return;
        HabitCalendar.putWeight(context, LocalDate.now(), draft);
        draw();
    }

    private void draw() {
        LocalDate today = LocalDate.now();
        List<LocalDate> days = HabitCalendar.days(context);
        drawGrid(today, days);
        drawWeights(today, days);
        applyMode();
        paintFocus();
        updateFigure();
    }

    private void drawGrid(LocalDate today, List<LocalDate> days) {
        grid.removeAllViews();
        cells.clear();
        todayCell = null;

        LocalDate first = today.withDayOfMonth(1);
        int count = first.lengthOfMonth();
        // Monday first: the squares before the first day are blanks that hold the week's shape.
        int lead = first.getDayOfWeek().getValue() - DayOfWeek.MONDAY.getValue();
        if (lead < 0) lead += 7;

        LinearLayout row = null;
        int total = lead + count;
        for (int i = 0; i < total; i++) {
            if (i % COLUMNS == 0) {
                row = newRow();
                grid.addView(row);
            }
            LocalDate day = i < lead ? null : first.plusDays(i - lead);
            View square = square(day, today, days);
            row.addView(square);
            cells.add(square);
        }
    }

    private void drawWeights(LocalDate today, List<LocalDate> days) {
        if (!weightOn) return;
        TreeMap<LocalDate, Float> weights = HabitCalendar.weights(context);
        float startKg = steps[0];
        float goalKg = steps[steps.length - 1];
        float nowKg = HabitCalendar.latestWeight(context, startKg);
        if (draft == null) draft = weights.containsKey(today) ? weights.get(today) : nowKg;
        startText.setText(kg1(startKg));
        nowText.setText(kg2(nowKg));
        goalText.setText(kg1(goalKg));
        draftText.setText(kg2(draft));
        LocalDate firstDay = weights.isEmpty() ? today : weights.firstKey();
        chart.setData(weights, firstDay, today, goalKg);
        streakText.setText(context.getString(R.string.habit_days_kept, days.size()));
        int level = HabitCalendar.bodyLevel(nowKg, steps);
        levelText.setText(context.getString(R.string.habit_weight_level, nowKg, level));
        body.setLevel(level);
    }

    /** One page at a time, and the cursor's way down changes with it: into the weight box, or off to the grid. */
    private void applyMode() {
        boolean weightMode = weightOn && mode == MODE_WEIGHT;
        grid.setVisibility(weightMode ? View.GONE : View.VISIBLE);
        weightPage.setVisibility(weightMode ? View.VISIBLE : View.GONE);
        streakText.setVisibility(weightMode ? View.VISIBLE : View.GONE);
        levelText.setVisibility(weightMode ? View.VISIBLE : View.GONE);
        panel.setNextFocusDownId(weightMode ? R.id.weightInput : R.id.grid);
    }

    /**
     * The pose follows the clock and nothing else: sitting, hungry, from eleven at night until eight
     * in the morning, standing through the rest of the day, and lifting weights - the only two hours
     * it lifts - from two until four in the afternoon. The hour is read again on the minute and on
     * every return to Home, so the figure changes over while the panel is on the screen and not
     * only at a restart.
     */
    private void updateFigure() {
        if (!weightOn) return;
        int hour = LocalTime.now().getHour();
        if (hour >= HUNGRY_FROM || hour < HUNGRY_TO) body.setPose(PixelBodyView.POSE_FAINT);
        else if (hour >= RUN_FROM && hour < RUN_TO) body.setPose(PixelBodyView.POSE_RUN);
        else body.setPose(PixelBodyView.POSE_STAND);
    }

    private View square(LocalDate day, LocalDate today, List<LocalDate> days) {
        View view = new View(context);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(cell, cell);
        if (cells.size() % COLUMNS != 0) params.setMarginStart(gap);
        view.setLayoutParams(params);
        int colour = PAD;
        if (day != null) {
            if (day.isAfter(today)) colour = FUTURE;
            else if (day.isBefore(start)) colour = BEFORE;
            else colour = HabitCalendar.ticked(days, day) ? DONE : MISSED;
            if (day.equals(today)) todayCell = view;
        }
        view.setBackground(shape(colour));
        return view;
    }

    private GradientDrawable shape(int colour) {
        GradientDrawable shape = new GradientDrawable();
        shape.setShape(GradientDrawable.RECTANGLE);
        shape.setCornerRadius(radius);
        shape.setColor(colour);
        return shape;
    }

    private LinearLayout newRow() {
        LinearLayout row = new LinearLayout(context);
        row.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        if (!cells.isEmpty()) params.topMargin = gap;
        row.setLayoutParams(params);
        return row;
    }

    private void paintFocus() {
        panel.setBackgroundResource(focused ? R.drawable.habit_panel_bg_focused : R.drawable.habit_panel_bg);
        for (View square : cells) {
            square.setScaleX(1f);
            square.setScaleY(1f);
        }
        if (focused && todayCell != null && mode == MODE_GRID) {
            todayCell.setScaleX(FOCUS_SCALE);
            todayCell.setScaleY(FOCUS_SCALE);
        }
    }

    private float clamp(float kg) {
        return Math.max(MIN_KG, Math.min(MAX_KG, kg));
    }

    /** Weights to one decimal beside each other, and to two where one number is being read on its own. */
    private static String kg1(float kg) {
        return String.format(Locale.US, "%.1f", kg);
    }

    private static String kg2(float kg) {
        return String.format(Locale.US, "%.2f", kg);
    }
}
