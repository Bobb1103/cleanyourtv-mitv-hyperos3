package com.gathin.tvhome;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.DashPathEffect;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.util.AttributeSet;
import android.view.View;

import java.time.LocalDate;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

/**
 * The weight page's curve: every weight recorded on the panel, drawn against the days since the run
 * began, with the newest one picked out in orange and the goal drawn as a line of its own once the
 * day's numbers come near it. Nothing here reads storage; HabitPanel hands it what to draw.
 *
 * The vertical scale follows the run rather than the whole 80 to 65 range on purpose. A first week
 * only moves a couple of kilos, and on a fixed scale that reads as a flat line along the top; so the
 * bottom of the plot is set by the lightest weight so far, and everything is squeezed down there as
 * the numbers fall, which shows the shape of the run from its second day on.
 */
public class WeightChartView extends View {

    private static final int CURVE = 0xFF97C459;
    private static final int GOAL = 0xFF97C459;
    private static final int TODAY = 0xFFF0A03C;
    private static final int GRID = 0x1AFFFFFF;
    private static final int AXIS = 0xFF6C7A70;

    /** Room kept for the numbers down the side and the dates along the bottom. */
    private static final float PAD_L = 24f;
    private static final float PAD_R = 6f;
    private static final float PAD_T = 8f;
    private static final float PAD_B = 14f;

    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint label = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final TreeMap<LocalDate, Float> records = new TreeMap<>();
    private float density = 2f;
    private LocalDate first;
    private LocalDate today;
    private float goal = Float.NaN;

    public WeightChartView(Context context, AttributeSet attrs) {
        super(context, attrs);
        density = getResources().getDisplayMetrics().density;
        label.setTextSize(8f * density);
        label.setColor(AXIS);
        try {
            Typeface pixel = getResources().getFont(R.font.press_start_2p);
            label.setTypeface(pixel);
        } catch (Exception ignored) {
            // Whatever the launcher's own font is then: a curve reads with any face.
        }
    }

    /**
     * What to draw. "first" is the day the x axis starts on, "today" the day it ends on: it stays
     * today even when today has no weight yet, so the run always reaches the right-hand edge.
     */
    void setData(Map<LocalDate, Float> values, LocalDate start, LocalDate end, float goalKg) {
        records.clear();
        if (values != null) records.putAll(values);
        first = start;
        today = end;
        goal = goalKg;
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (records.isEmpty() || first == null || today == null) return;
        float left = PAD_L * density;
        float right = getWidth() - PAD_R * density;
        float top = PAD_T * density;
        float bottom = getHeight() - PAD_B * density;
        if (right <= left || bottom <= top) return;

        float high = Float.NEGATIVE_INFINITY;
        float low = Float.POSITIVE_INFINITY;
        for (Float kg : records.values()) {
            high = Math.max(high, kg);
            low = Math.min(low, kg);
        }
        float topKg = high + 0.3f;
        float bottomKg = Math.max(low, goal) - 0.7f;
        if (bottomKg >= topKg) bottomKg = topKg - 1f;
        long days = Math.max(1L, today.toEpochDay() - first.toEpochDay());

        // Three faint lines with their weights down the side, so the fall can be read in kilos.
        for (int i = 0; i < 3; i++) {
            float kg = topKg - (topKg - bottomKg) * i / 3f;
            float y = yOf(kg, topKg, bottomKg, top, bottom);
            paint.setColor(GRID);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(density);
            canvas.drawLine(left, y, right, y, paint);
            canvas.drawText(String.format(Locale.US, "%.0f", kg), 2 * density, y + 3 * density, label);
        }

        if (!Float.isNaN(goal) && goal >= bottomKg && goal <= topKg) {
            float y = yOf(goal, topKg, bottomKg, top, bottom);
            paint.setColor(GOAL);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(density);
            paint.setPathEffect(new DashPathEffect(new float[]{4 * density, 3 * density}, 0f));
            canvas.drawLine(left, y, right, y, paint);
            paint.setPathEffect(null);
        }

        float px = 0f;
        float py = 0f;
        boolean penDown = false;
        LocalDate lastDay = null;
        paint.setStyle(Paint.Style.STROKE);
        paint.setColor(CURVE);
        paint.setStrokeWidth(2f * density);
        for (Map.Entry<LocalDate, Float> entry : records.entrySet()) {
            LocalDate day = entry.getKey();
            if (day.isBefore(first) || day.isAfter(today)) continue;
            float x = xOf(day, first, days, left, right);
            float y = yOf(entry.getValue(), topKg, bottomKg, top, bottom);
            if (penDown) canvas.drawLine(px, py, x, y, paint);
            px = x;
            py = y;
            penDown = true;
            lastDay = day;
        }
        // The newest weight gets the orange square. With nothing weighed today yet, an orange dotted
        // line carries the run on to today's edge instead, and no point claims to have been weighed.
        if (lastDay != null) {
            if (lastDay.equals(today)) {
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(TODAY);
                canvas.drawRect(px - 2.2f * density, py - 2.2f * density,
                        px + 2.2f * density, py + 2.2f * density, paint);
            } else {
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(CURVE);
                canvas.drawRect(px - 1.4f * density, py - 1.4f * density,
                        px + 1.4f * density, py + 1.4f * density, paint);
                paint.setColor(TODAY);
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(density);
                paint.setPathEffect(new DashPathEffect(new float[]{3 * density, 3 * density}, 0f));
                canvas.drawLine(px, py, xOf(today, first, days, left, right), bottom, paint);
                paint.setPathEffect(null);
            }
            dateLabel(canvas, first, left, bottom);
            dateLabel(canvas, lastDay, xOf(lastDay, first, days, left, right), bottom);
            dateLabel(canvas, today, xOf(today, first, days, left, right), bottom);
        }
    }

    /** Vertical: kilos to pixels, top of the plot being the heaviest end of the window. */
    private static float yOf(float kg, float topKg, float bottomKg, float top, float bottom) {
        return top + (topKg - kg) * (bottom - top) / (topKg - bottomKg);
    }

    /** Horizontal: a day to pixels across all the days the run has been going. */
    private static float xOf(LocalDate day, LocalDate first, long days, float left, float right) {
        long offset = Math.max(0L, day.toEpochDay() - first.toEpochDay());
        return left + offset * (right - left) / days;
    }

    private void dateLabel(Canvas canvas, LocalDate day, float x, float baseline) {
        String text = String.format(Locale.US, "%d/%d", day.getMonthValue(), day.getDayOfMonth());
        float width = label.measureText(text);
        float leftEdge = Math.min(Math.max(x - width / 2f, 0f), getWidth() - width);
        canvas.drawText(text, leftEdge, baseline + 11 * density, label);
    }
}
