# Pi-Reader Project Context

## Hardware
- Raspberry Pi Zero 2 WH
- Waveshare 3.7" E-Ink display (480x280px, 1-bit black/white)
- PiSugar 2 battery HAT (I2C communication)
- Controlled via 4 physical buttons (w=up, s=down, p=select, q=back)

## Architecture
- `main.py` — event loop, listens for input, calls screen.handle_key()
- `screens/` — one file per screen. Each has draw() and handle_key()
- `config/display_manager.py` — all e-ink refresh logic lives here
- `config/fonts.py` — all fonts defined once here
- `app/` — Flask server for WiFi book uploads (port 5000)
- `utils/scanner.py` — scans library folder, returns book list
- `content/library/` — converted .txt books
- `content/books/` — raw uploaded files (epub, pdf, etc)
- `content/comics/` — comic files

## Key Constraints
- Display is 1-bit (black/white only, no greyscale in current config)
- Pi Zero is slow — avoid heavy computation on screen render
- Partial refresh is faster but leaves ghosting; deep_clear() fixes it
- All paths are relative to /home/miquel/pi-reader/

## Known Bugs (fix as we touch each file)
- ~~reader.py has unused `lines` parameter in __init__~~ fixed
- ~~comics.py references MenuScreen without importing it~~ fixed
- ~~No scroll guards in reader.py (can go past end/start of book)~~ fixed
- Hardcoded absolute paths in fonts.py and comics.py still (partially centralized)

## Phase 1: Solid Reader (current focus)
- [x] Battery % on every screen (PiSugar2 via I2C)
- [x] Reader: fix word-wrap (no mid-word breaks)
- [x] Reader: scroll guards (can't go past end/start)
- [ ] Reader: remember last page when exiting

## Phase 2: Delight
- [ ] RSVP mode
- [ ] Reading stats
- [ ] Better typography
- [ ] Sleep/wake power management

## Code Style
- Python, no type hints needed, keep it readable
- Each screen is self-contained — import other screens lazily (inside functions)
- Never put display logic outside of screens/ or config/
- When fixing a file, fix known bugs in that file too