package com.gathin.tvhome;

import android.content.Context;
import android.content.SharedPreferences;

import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * The habit calendar's records. A ticked day is one date, kept as text in the app's own preferences:
 * a list of dates is small (a few hundred bytes a year), survives a reboot like any other preference,
 * and needs no storage permission, which the launcher would not be granted on Android 11 and later.
 *
 * Nothing here touches the screen: the panel reads it and draws. The date arithmetic is pure, so the
 * JVM tests can check a streak across a month boundary without an emulator.
 */
final class HabitCalendar {

    private static final String PREFS = "habit_calendar";
    private static final String KEY_DAYS = "days";
    private static final String SEPARATOR = ",";
    /** Weights, kept beside the days as "2026-10-19=77.5" pairs: the date says when, the number says how much. */
    private static final String KEY_WEIGHTS = "weights";
    private static final String ASSIGN = "=";

    private HabitCalendar() {
    }

    /** The days ticked, oldest first. Never null. */
    static List<LocalDate> days(Context context) {
        String raw = prefs(context).getString(KEY_DAYS, "");
        List<LocalDate> out = new ArrayList<>();
        if (raw == null || raw.isEmpty()) return out;
        for (String part : raw.split(SEPARATOR)) {
            LocalDate day = parse(part);
            if (day != null && !out.contains(day)) out.add(day);
        }
        Collections.sort(out);
        return out;
    }

    static boolean ticked(List<LocalDate> days, LocalDate day) {
        return days.contains(day);
    }

    /** Ticks the day, or unticks it. Returns whether the day is ticked now. */
    static boolean toggle(Context context, LocalDate day) {
        List<LocalDate> days = days(context);
        boolean on = ticked(days, day);
        if (on) days.remove(day);
        else {
            days.add(day);
            Collections.sort(days);
        }
        save(context, days);
        return !on;
    }

    /**
     * How many days in a row end at today. Today not ticked yet counts from yesterday, so the number
     * only breaks the morning after a missed day, not the moment the clock passes midnight.
     */
    static int streak(List<LocalDate> days, LocalDate today) {
        LocalDate cursor = ticked(days, today) ? today : today.minusDays(1);
        int count = 0;
        while (ticked(days, cursor)) {
            count++;
            cursor = cursor.minusDays(1);
        }
        return count;
    }

    /** Days from today to the target, 0 once it is today or past. Negative days read as 0. */
    static int daysTo(LocalDate today, LocalDate target) {
        if (target == null || !target.isAfter(today)) return 0;
        return (int) (target.toEpochDay() - today.toEpochDay());
    }

    /**
     * Records days kept before the calendar existed. Newly-read dates are added once: take one back and
     * stay taken back, whether it comes from here or from OK.
     */
    static void seed(Context context, String raw) {
        if (raw == null || raw.trim().isEmpty()) return;
        List<LocalDate> days = days(context);
        List<LocalDate> additions = new ArrayList<>();
        for (String part : raw.split(SEPARATOR)) {
            LocalDate day = parse(part);
            if (day != null && !days.contains(day) && !additions.contains(day)) additions.add(day);
        }
        if (additions.isEmpty()) return;
        days.addAll(additions);
        Collections.sort(days);
        save(context, days);
    }

    /**
     * The first day of the run: config.xml habit_start when it is set, otherwise the earliest day
     * ticked, otherwise today, so a fresh calendar draws one day instead of none.
     */
    static LocalDate start(Context context, String configured) {
        LocalDate parsed = parse(configured);
        if (parsed != null) return parsed;
        List<LocalDate> days = days(context);
        return days.isEmpty() ? LocalDate.now() : days.get(0);
    }

    /**
     * Every weight recorded, oldest day first. Never null; empty until something has been typed in.
     * The figure's shape and the curve are both read from this and from nothing else, which is why a
     * long break can put the weight back on: there is nothing to hold a shape that has not been kept.
     */
    static TreeMap<LocalDate, Float> weights(Context context) {
        String raw = prefs(context).getString(KEY_WEIGHTS, "");
        TreeMap<LocalDate, Float> out = new TreeMap<>();
        if (raw == null || raw.isEmpty()) return out;
        for (String part : raw.split(SEPARATOR)) {
            int split = part.indexOf(ASSIGN);
            if (split <= 0) continue;
            LocalDate day = parse(part.substring(0, split));
            if (day == null) continue;
            try {
                out.put(day, Float.parseFloat(part.substring(split + 1).trim()));
            } catch (NumberFormatException ignored) {
                // A hand-edited preference no one can read is simply left out of the curve.
            }
        }
        return out;
    }

    /** Records (or corrects) one day's weight: the same day twice keeps only the newer number. */
    static void putWeight(Context context, LocalDate day, float kg) {
        TreeMap<LocalDate, Float> all = weights(context);
        all.put(day, kg);
        StringBuilder text = new StringBuilder();
        for (Map.Entry<LocalDate, Float> entry : all.entrySet()) {
            if (text.length() > 0) text.append(SEPARATOR);
            text.append(entry.getKey()).append(ASSIGN).append(entry.getValue());
        }
        prefs(context).edit().putString(KEY_WEIGHTS, text.toString()).apply();
    }

    /**
     * The newest weight typed in, or "fallback" when nothing has been recorded yet (usually the weight
     * the run started from, so the figure begins round rather than absent).
     */
    static float latestWeight(Context context, float fallback) {
        TreeMap<LocalDate, Float> all = weights(context);
        if (all.isEmpty()) return fallback;
        List<LocalDate> keys = new ArrayList<>(all.keySet());
        return all.get(keys.get(keys.size() - 1));
    }

    /** Weights known before this page existed, "date=kg" pairs recorded once. Newer preferred entries win. */
    static void seedWeights(Context context, String raw) {
        if (raw == null || raw.trim().isEmpty()) return;
        TreeMap<LocalDate, Float> all = weights(context);
        for (String part : raw.split(SEPARATOR)) {
            int split = part.indexOf(ASSIGN);
            if (split <= 0) continue;
            LocalDate day = parse(part.substring(0, split));
            if (day == null) continue;
            if (all.containsKey(day)) continue;   // something already typed for that day wins
            try {
                putWeight(context, day, Float.parseFloat(part.substring(split + 1).trim()));
            } catch (NumberFormatException ignored) {
                // ignore
            }
        }
    }

    /**
     * Which of the five bodies a weight draws: the steps run from the weight the programme began at
     * down to the one being aimed for, and each band between two neighbouring steps is one shape.
     */
    static int bodyLevel(float kg, float[] steps) {
        if (steps == null || steps.length < 2) return 0;
        for (int i = 0; i < steps.length - 1; i++) {
            if (kg <= steps[i] && kg > steps[i + 1]) return i;
        }
        return kg >= steps[0] ? 0 : steps.length - 2;
    }

    static LocalDate parse(String value) {
        if (value == null) return null;
        String text = value.trim();
        if (text.isEmpty()) return null;
        try {
            return LocalDate.parse(text);
        } catch (DateTimeParseException e) {
            return null;
        }
    }

    private static void save(Context context, List<LocalDate> days) {
        StringBuilder text = new StringBuilder();
        for (int i = 0; i < days.size(); i++) {
            if (i > 0) text.append(SEPARATOR);
            text.append(days.get(i));
        }
        prefs(context).edit().putString(KEY_DAYS, text.toString()).apply();
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
