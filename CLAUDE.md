# Pi-Reader Project Context

## Hardware
- Raspberry Pi Zero 2 WH
- Waveshare 3.7" E-Ink display (480×280px, 1-bit black/white, landscape)
- PiSugar 2 battery HAT (I2C — currently not responding, see Known Issues)
- 4 physical buttons on BCM 5/6/13/26 (pins 29/31/33/37, GND 39) — wired on a breadboard, GPIO_ENABLED=True
- E-paper connected by cable (not as HAT): RST 17, DC 25, CS 8, BUSY 24, PWR 18, MOSI 10, SCLK 11

## Architecture

```
main.py                  — EReader: event loop, GPIO/keyboard input, auto-sleep, boot-to-last-book
screens/
  menu.py                — Main menu (Library, Highlights, Statistics, Upload, Settings) + stats panel
  library.py             — Book list with pagination, truncated titles
  reader.py              — Book reader: pixel-width wrap, justified text, headings, bookmarks, session stats
  reader_menu.py         — p in reader: Save highlight, Contents, RSVP, Font size, Sync to Daybook
  toc_screen.py          — Table of contents from detected headings
  rsvp.py                — RSVP word-by-word reader
  saved_screen.py        — Browse saved highlights (+ save_highlight())
  stats_screen.py        — Reading statistics
  config_screen.py       — Settings (sleep timeout, default font, daily goal)
  upload_screen.py       — Shows IP, runs the Flask upload server only while on this screen
  sleep_screen.py        — Builds the Obelix shutdown/sleep image with live date
config/
  display_manager.py     — init, deep_clear, draw_screen, sleep, wake; display.lock; fast_buffer()
  display.py             — Waveshare EPD3in7 hardware init (480×280)
  fonts.py               — All fonts loaded once (Literata, fallback to default)
  paths.py               — BASE_DIR + all content/asset paths in one place
  ui_components.py       — draw_header(), draw_footer(); battery stub (returns None)
app/
  __init__.py            — Flask app + secret key
  file_transfer.py       — POST / upload books (100 MB cap), GET /highlights
  text_converter.py      — ebook-convert wrapper (Calibre), one conversion at a time; .txt copied as-is
utils/
  text_parser.py         — parse() → List[Line(text, kind)] where kind=body/heading/gap; wrap_px()
  scanner.py             — get_books_list() from content/library/, skips dotfiles
  stats.py               — reading sessions in content/stats.json, streak, totals
  config_manager.py      — content/config.json settings with defaults
  daybook_sync.py        — fire-and-forget calls to the Daybook API (background threads)
  battery.py             — PiSugar2 I2C read (unused — see Known issues)
tests/                   — unittest for pure modules: python3 -m unittest discover tests
tools/
  extract_logo.py        — One-time: generate assets/sleep_logo.png from obelix_source.png
  shutdown_screen.py     — Called by systemd on shutdown to draw Obelix before halt
content/
  library/               — Converted .txt + .meta.json per book; .bookmarks.json (gitignored)
  books/                 — Raw uploads (epub, pdf, etc) (gitignored except .gitkeep)
  highlights.json, stats.json, config.json — device state (not in git)
pi-reader.service          — systemd unit: runs main.py on boot, logs to the journal
pi-reader-shutdown.service — systemd unit: draws Obelix on sudo shutdown
```

## Display constants (used in every screen)
```python
_W = 480      # canvas width  (epd.height in landscape orientation)
_H = 280      # canvas height (epd.width  in landscape orientation)
_HEADER_H = 54  # black header bar height (draw_header)
```

## Key constraints
- 1-bit display — no greyscale. Use threshold (not dither) for line art, Floyd-Steinberg for photos.
- Pi Zero 2 is slow — avoid heavy computation in draw(). Pre-compute in __init__.
- deep_clear() = black flash → white → ready. EReader.switch_to() does it, then calls screen.draw().
  Screens opened via switch_to must NOT draw in __init__ (double refresh). Overlay screens
  (reader_menu, toc) are assigned to ereader.current_screen directly and do draw in __init__.
- Every draw is a full A2 refresh (use_partial is ignored). Always send frames via display.* —
  it holds display.lock and uses fast_buffer() instead of the driver's slow per-pixel getbuffer().
- Key handling and auto-sleep run under EReader._lock. Background threads that draw (RSVP,
  upload screen) must check they are still current_screen and not sleeping.
- Screens may define `on_sleep()` (called before auto-sleep) and a `busy` property (blocks auto-sleep).
- Reading position is a body-word index (bookmark 'word'), never a page number — pages
  change with font size. BookScreenReader(start_word=..., font_size=...).
- Text wrap must use the reader's cached `_measure` so justified lines never get negative gaps.
- All imports of other screens must be lazy (inside functions) to avoid circular imports.
- Never put display logic outside screens/ or config/.

## Navigation map
```
Boot → last-read book (exact position) OR Menu if no book opened yet
       (python3 main.py --menu forces the menu)

Main Menu
├── Library     → select book → Reader
│                 In Reader: s/w=page, p=reader options, q=back to library
│                 Reader options: Save highlight, Contents, RSVP mode, Font, Sync to Daybook
├── Highlights  → saved highlights browser (w/s=scroll, q=back)
├── Statistics  → reading stats
├── Upload      → shows IP, runs Flask on port 5000 until you press q
└── Settings    → sleep timeout, default font, daily goal (w/s change, p next row)
```

## Button mapping
```
w = up / prev page
s = down / next page
p = select / reader options
q = back
z = quit (keyboard fallback only)
```

## RSVP
- Reader options → RSVP mode. Starts at the first word of the current page.
- Controls: p=pause/resume, w=slower, s=faster, q=back to reader at the RSVP word.
- Speeds: 60 / 100 / 150 / 200 / 250 WPM. Each word is a full refresh, so real speed is
  capped by panel refresh time; the loop subtracts draw time from the per-word delay.

## Daybook
- API at http://100.67.252.76:8000 (Tailscale), configurable via content/config.json daybook_url.
- Works today: GET /books, POST /books (author is required — send '').
- push_highlight() posts to /books/{id}/highlights, which Daybook does NOT have yet (404).
- Daybook /days/{date} is PATCH, and patching `notes` would overwrite the user's notes — don't.

## Systemd services
- `pi-reader-shutdown.service` — draws Obelix before halt/reboot. Installed at:
  `/etc/systemd/system/pi-reader-shutdown.service`
- `pi-reader.service` — auto-starts main.py on boot (see setup below)

## Known issues
- **Battery shows nothing**: PiSugar2 not responding on I2C — `i2cdetect -y 1` is empty even with
  the display on a cable instead of the HAT, so it's the PiSugar's pogo-pin contact, not the HAT.
- **Upload server has no auth**: only runs while the Upload screen is open, but anyone on the
  same network/tailnet can upload or read /highlights during that time.

## Setup on a fresh Pi
```bash
# 1. Clone
git clone https://github.com/Miquelfs/pi-reader.git ~/pi-reader
cd ~/pi-reader

# 2. System deps
sudo apt install calibre poppler-utils -y
pip3 install Flask Pillow smbus2 gpiozero --break-system-packages

# 3. Generate sleep logo
python3 tools/extract_logo.py

# 4. Install systemd services
sudo cp pi-reader-shutdown.service /etc/systemd/system/
sudo cp pi-reader.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pi-reader-shutdown.service
sudo systemctl enable pi-reader.service

# 5. Enable I2C (if not already)
sudo raspi-config nonint do_i2c 0
```

## Development workflow
1. Edit code locally on Mac in VSCode
2. `git add ... && git commit -m "..." && git push`
3. On Pi: `cd ~/pi-reader && git pull`
4. Restart service: `sudo systemctl restart pi-reader.service`
   Logs: `journalctl -u pi-reader -f`
   Or test manually (stop the service first): `python3 main.py --menu`
5. Tests (Mac or Pi): `python3 -m unittest discover tests`

## Code style
- Python, no type hints needed
- No comments unless the WHY is non-obvious
- Each screen is self-contained — lazy imports inside functions only
- Constants at top of each screen file (_W, _H, _MARGIN etc)
- Screens all follow the same pattern: __init__(ereader, **kwargs), draw(), handle_key(key)
