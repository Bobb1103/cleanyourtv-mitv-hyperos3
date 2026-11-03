# Tools

Two things live in `tools/`: the scripts this branch added while building the habit
panel and the pixel figure, and the ones that came with upstream CleanYourTV. Every
script is plain Python 3 and none of them needs a package installed except the two
mock-up generators, which want Pillow.

Point them at your TV with `TV_HOST` (and `TV_PORT` if it is not 5555):

```bash
export TV_HOST=192.168.1.50:5555      # or TV_HOST=192.168.1.50 and TV_PORT=5555
```

## Added by this branch

| Script | What it is for |
| --- | --- |
| `tv_check.py` | Drives the TV over ADB for the panel checks. Reconnects before **every** command, because the link to a TV drops constantly, screenshots each step, and answers "is the panel showing?" by counting its green squares. Import it rather than running it: `from tv_check import adb, press, shot, green, focus, texts`. |
| `panel_visible.py` | The measurement behind that answer: `read_png(path)` decodes a screenshot with no third-party library, `count_green(...)` counts the green "day kept" pixels in the panel's patch of screen. Roughly 21 500 means the calendar is fully drawn, a handful means it has faded out. It is how the show/hide rule was verified without eyeballing screenshots. |
| `png_probe.py` | Decodes a PNG the same way and reports where the dock band sits and how far each tile runs, for checking layout numbers. |
| `preview_lift.py` | Draws the barbell pose's two frames into `preview-lift.png`, using the same numbers and the same draw order as `PixelBodyView.drawLifting`. Editing a pixel figure two minutes at a time through Gradle is no fun; this puts the layout on screen in a second. It mirrors the code by hand, so keep the two in step. |
| `gen_faint_mock.py` | The mock-up sheet the "starving" redesign was chosen from: three candidates plus the old one, on the same 16x26 grid, written to `mock-faint-redesign.png`. Needs Pillow. |
| `gen_lift_mock.py` | The same for the exercise pose: three barbell candidates plus the running pose they replaced, written to `mock-lift-redesign.png`. Needs Pillow. |
| `gh_publish.py` | Puts this repository on GitHub: creates it if it is not there (description and topics in one go), renames `master` to `main`, rewrites the commit author to the signed-in account's noreply address, then pushes. The token comes from `GITHUB_TOKEN` or from the Git Credential Manager store and is handed to that one `git push` through the environment, so it never reaches `.git/config`. `python tools/gh_publish.py [--private] [--name X]`. |

## From upstream

| Script | What it is for |
| --- | --- |
| `check.py` | What a firmware update undid, compared with the debloat list that was applied. `--fix` puts it back. |
| `recovery.py` | Saves the state a debloat list is about to change, so undo really means undo. `--save`, `--commands`. |
| `privacy.py` | Audits what the TV runs for voice, ACR and telemetry, with the evidence for each package name, and can write the result straight out as a debloat list. |
| `bench.py` | The launcher's headline numbers on a real TV: key latency, jank, cold start, return to Home, memory. |
| `trace.py`, `trace_report.py`, `flamechart.py` | Record Perfetto traces around a scenario, compare two runs, and draw a before/after flame chart for a pull request. |
| `screendiff.py` | Compares a before and an after screenshot pixel by pixel and draws the pair - a performance change should look identical. |
| `live_check.py`, `live_verify.py`, `live_rate.py` | Test live-TV source URLs: does it answer, does it look like a playlist, do sampled channels actually play. The 11 working sources in [live-sources.md](live-sources.md) came out of these. |
| `manage.py` | One place for add-ons, themes and switches: what they are, what is on the TV, and installing or removing them the way their creator documented. |
| `tv.py`, `relay.py`, `b64push.py`, `b64pull.py`, `adb-closed.py` | Talking to the TV when the ordinary route is unavailable: a pure-Python ADB client, a local port forwarder for sandboxed assistants, base64 file transfer through plain shell commands, and a check that the network ADB port really is closed. |
| `scenes_wallpapers.py`, `race_calendar.py`, `readme_stats.py`, `readme_featured.py`, `readme_card.py`, `gen_tables.py` | Generate artwork and the README figures - the 14 scene wallpapers as SVG from code, the F1 calendar for a theme, the stat strip and card, and the TV tables in the READMEs. |

## Notes

- Only `check.py --fix`, `recovery.py --commands` and `manage.py` change anything on the
  TV; the rest read, measure or draw. The scripts this branch added are read-only
  apart from `press()` sending key events.
- `tools/venv/` used to hold a local virtualenv with Pillow. It is not in the
  repository (see `.gitignore`) - create your own if you want to run the generators.
