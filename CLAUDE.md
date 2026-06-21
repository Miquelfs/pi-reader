# Pi-Reader Project Context

## Hardware
- Raspberry Pi Zero 2 WH
- Waveshare 3.7" E-Ink display (480×280px, 1-bit black/white, landscape)
- PiSugar 2 battery HAT (I2C — currently not responding, see Known Issues)
- 4 physical buttons to be wired (BCM pins 17/22/23/27 reserved) — keyboard fallback active

## Architecture

```
main.py                  — EReader class: event loop, GPIO setup, sleep/wake, battery check
screens/
  menu.py                — Main menu (Biblioteca, Guardats, Puja un llibre, Configuració)
  library.py             — Book list with pagination, truncated titles
  librarymenu.py         — Intermediate menu (currently just Llibres — one option)
  reader.py              — Book reader: paragraph-aware, headings, bookmarks, highlight save
  rsvp.py                — RSVP word-by-word reader (built, needs entry point wired)
  saved_screen.py        — Browse saved highlights
  upload_screen.py       — Shows IP + starts Flask server for WiFi uploads
  sleep_screen.py        — Builds the Obelix shutdown/sleep image with live date
config/
  display_manager.py     — init, deep_clear, draw_screen, sleep, wake
  display.py             — Waveshare EPD3in7 hardware init (480×280)
  fonts.py               — All fonts loaded once (Literata, fallback to default)
  paths.py               — BASE_DIR + all content/asset paths in one place
  ui_components.py       — draw_battery_icon() with inverted mode + I2C caching
app/
  __init__.py            — Flask app + secret key
  file_transfer.py       — POST /  upload books, trigger conversion
  text_converter.py      — ebook-convert wrapper (Calibre), skips dotfiles
utils/
  battery.py             — PiSugar2 I2C read, probes 0x75 and 0x57, voltage→% curve
  scanner.py             — get_books_list() from content/library/, skips dotfiles
  text_parser.py         — parse() → List[Line(text, kind)] where kind=body/heading/gap
tools/
  extract_logo.py        — One-time: generate assets/sleep_logo.png from obelix_source.png
  shutdown_screen.py     — Called by systemd on shutdown to draw Obelix before halt
assets/
  obelix_source.png      — Source image for sleep screen
  sleep_logo.png         — Generated 1-bit sleep/shutdown screen
content/
  library/               — Converted .txt books (gitignored except .gitkeep)
  books/                 — Raw uploads (epub, pdf, etc) (gitignored except .gitkeep)
  comics/                — Comic files (gitignored except .gitkeep)
  highlights.json        — Saved page highlights (written by reader.py)
pi-reader-shutdown.service — systemd unit: draws Obelix on sudo shutdown
```

## Display constants (used in every screen)
```python
_W = 480      # canvas width  (epd.height in landscape orientation)
_H = 280      # canvas height (epd.width  in landscape orientation)
_HEADER_H = 52  # black header bar height (+ 4px drawn solid = 52 total)
```

## Key constraints
- 1-bit display — no greyscale. Use threshold (not dither) for line art, Floyd-Steinberg for photos.
- Pi Zero 2 is slow — avoid heavy computation in draw(). Pre-compute in __init__.
- deep_clear() = black flash → white → ready. Use between screen transitions to remove ghosting.
- Partial refresh is faster but leave ghost. Full refresh used everywhere currently.
- All imports of other screens must be lazy (inside functions) to avoid circular imports.
- Never put display logic outside screens/ or config/.

## Navigation map
```
Boot → last-read book (exact page) OR Menu if no book opened yet

Main Menu
├── Biblioteca     → Library screen → select book → Reader
│                    In Reader: s/w=page, p=save highlight, q=back to library
├── Guardats       → Saved highlights browser (w/s=scroll, q=back)
├── Puja un llibre → Upload screen: shows IP, starts Flask on port 5000
└── Configuració   → not yet implemented
```

## Button mapping
```
w = up / prev page
s = down / next page
p = select / save highlight (in reader)
q = back
z = quit (keyboard fallback only)
```

## RSVP
- Screen exists at screens/rsvp.py — fully implemented
- Entry: not yet wired. Plan: long-press p in reader, OR add as option in a reader submenu
- Controls when active: p=pause/resume, w=slower, s=faster, q=back to reader
- Speed options: 150 / 200 / 250 WPM (e-ink refresh limits higher speeds)
- Receives word list + start position from BookScreenReader

## Systemd services
- `pi-reader-shutdown.service` — draws Obelix before halt/reboot. Installed at:
  `/etc/systemd/system/pi-reader-shutdown.service`
- `pi-reader.service` — auto-starts main.py on boot (see setup below)

## Known issues
- **Battery shows `—%`**: PiSugar2 not responding on I2C (probes 0x75 and 0x57).
  Likely Waveshare HAT interfering with I2C bus when both are connected.
  Debug: run `sudo i2cdetect -y 1` with only PiSugar2 attached (Waveshare disconnected).
- **RSVP unreachable**: built but no UI entry point yet.
- **librarymenu.py is redundant**: only has one option (Llibres). Can be removed
  once we're confident no other categories are coming back.

## Setup on a fresh Pi
```bash
# 1. Clone
git clone https://github.com/Miquelfs/pi-reader.git ~/pi-reader
cd ~/pi-reader

# 2. System deps
sudo apt install calibre poppler-utils -y
pip3 install Flask Pillow smbus2 gpiozero pdf2image --break-system-packages

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
   Or test manually: `python3 main.py`

## Code style
- Python, no type hints needed
- No comments unless the WHY is non-obvious
- Each screen is self-contained — lazy imports inside functions only
- Constants at top of each screen file (_W, _H, _MARGIN etc)
- Screens all follow the same pattern: __init__(ereader, **kwargs), draw(), handle_key(key)
