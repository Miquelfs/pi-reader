# Pi-Reader Case Design Specification

## Purpose
Hardware measurements and design decisions for a 3D-printable enclosure. Front/back
views below are as the reader is held (right hand, landscape).

## Layout (decided 2026-11-03)
One-handed landscape reader. The Pi stack sits under the button wing, so the heavy,
thick part is in the right hand, like a book's spine or a Kindle Oasis grip:

```
 FRONT                                    thin section          │ grip
┌──────────────────────────────────────┬───────┐
│                                      │   ◦   │  Back
│          e-paper 101.8 × 63.1        │   ▲   │  Up / prev page
│     (orange flex on the LEFT edge)   │   ▼   │  Down / next page
│                                      │   ●   │  Select
├──────────────────────────────────────┴───────┤
│  chin: display cable plug (PH2.0)            │◄ PiSugar charge port + power
└──────────────────────────────────────────────┘   switch slider on RIGHT wall
```

- Display is NOT plugged into the Pi. Its 40-pin socket (on the back, along the TOP edge)
  is unused. Display connects through its 8-wire PH2.0 cable (connector on the BOTTOM edge).
- Pi + PiSugar lie crossways on the RIGHT end of the display back (free strip beside the
  socket), overhanging the board edge into the wing so the ports face the right wall.
  Foam on the display board, then the printed Pi spacer (4 mm), then the battery. The spacer
  lifts the stack so the battery overhanging the wing rests on the button retainer's rails,
  not on the switches.
- Header faces the back lid. Pin 1 (SD card end) toward the TOP.
- Text orientation: reads upright in this layout with no software flip (verified 2026-11-03).
- Stepped profile: thin section behind the screen (socket height), deep grip behind the
  wing (Pi stack).

## Decisions from measurements (2026-11-03)
- Switches are tall 6×6 (9.96 mm). Their plungers poke 1 mm through 4.2 mm holes in the
  front panel; no printed caps.
- Display cable and buttons stay on plug-on jumpers (no soldering on the Pi). With the wires
  bent flat right at the plugs they stand 25 mm above the Pi board: grip 62.7 mm.
  (Soldering wires to the pin tips would give ~50 mm; plugging the display straight onto the
  Pi covers the button pins and needs a splitter board or USB keypad — v2 ideas.)
- Back shell prints back-face down with supports touching the build plate only.

## Wiring
| Signal | Pi physical pin | BCM |
|---|---|---|
| Display VCC / GND | 1 / 6 | — |
| Display DIN / CLK / CS | 19 / 23 / 24 | 10 / 11 / 8 |
| Display DC / RST / BUSY | 22 / 11 / 18 | 25 / 17 / 24 |
| Button Up / Down | 29 / 31 | 5 / 6 |
| Button Select / Back | 33 / 37 | 13 / 26 |
| Button ground (chained) | 39 | — |

## Buttons
- 6×6 tactile, 9.96 mm tall, ~14 mm pitch, single column in the wing:
  Back, Up, Down, Select (top → bottom).
- Each button: signal wire on one leg, ground on the diagonally opposite leg. Ground legs
  chained with short solid-core links; one ground wire to pin 39.
- Legs bent flat before soldering to keep the assembly thin; Kapton over the legs.
- Mounted in the printed retainer (4 pockets, legs through slots in its floor, soldered on
  its back), screwed to two posts in the front shell. Plungers poke through the front.

## Case
- Front shell: screen window with ~1.5 mm lip over the glass edge, wing with 4 cap holes,
  4 screw bosses.
- Back shell: stepped. Ribs press the display board onto the front lip through foam pads;
  walls locate the Pi stack; right-wall openings for the PiSugar charge port and a recessed
  slider that drives the PiSugar power switch.
- Joined with 4 self-tapping M2.5 screws into printed bosses (no inserts needed).
- A few vent slots over the Pi.
- Walls 2 mm minimum. PLA or PETG, 0.2 mm layers. Minimal look, slight edge chamfer.

## Power
- Off for storage/travel: PiSugar slide switch, flicked through a slot in the right wall with a
  toothpick or SIM pin. ON = toward the top. (A printed slider was dropped: its stem would
  scrape the PiSugar PCB edge and the Pi's HDMI connector while the back shell closes.)
- Safe shutdown first (planned software): long-press Back ~3 s → Obelix screen → halt,
  then slide the switch off. Avoids SD-card corruption from hard power cuts.
- On: slide the switch on → boots straight into the last book.

## Measurements
| Component | Measurement | Value |
|---|---|---|
| Display board | Length × Width | 101.81 × 63.11 mm |
| Display board with socket | Glass front to socket top | 22 mm |
| Display 40-pin socket | Position along long edge | ~15–68 mm from orange-flex end |
| Pi + PiSugar + battery | Battery back to header pin tips | 30.62 mm |
| Display + foam + Pi stack | Glass front to header pin tips | 37.11 mm |
| Full stack, display plugged on Pi (abandoned layout) | Total thickness | 42.21 mm |
| Pi ↔ PiSugar board gap | At header end | ~1–2 mm — too tight to solder under the header |
| Display board | "8 mm" — includes the cable connector; glass→pin tips (37.11) minus Pi stack (30.62) leaves 6.49 mm for board + glass + foam |
| Display glass | W × H | 92.15 × 57.2 mm |
| Image area | W × H (datasheet) | 81.12 × 47.32 mm — confirm with tools/frame_test.py |
| Image area (frame_test.py) | Board edge → frame: left / right / bottom / top | 14.21 / 10.62 / 10.10 / 11.12 mm — size doesn't match 480:280, so the window uses this centre with the datasheet size |
| Board height incl. cable plug + bend | | 77.77 mm (plug sticks out 14.7) |
| Pi stack | Overhang past board edge | 0 when measured; the case sets it to the wing (ports at the wall) |
| PiSugar charge port | Along the PiSugar from its SD-card end | ends at 55.81 mm (centre ~52); ~25.8 mm behind the case front (from side photo) |
| PiSugar switch (white, under the PiSugar board) | Along the PiSugar from its SD-card end | 12.8 (ON) / 13.92 mm; ON = toward the SD-card end; lever ~26 mm behind the case front, nearly flush with the PCB edge |
| PiSugar board | Thickness / gap to Pi | ~1.0 / ~0.8 mm (side photo) |
| Pi stack with jumpers on | Glass front to furthest wire | 60 mm loose; case assumes ~49 with wires cut short and bent tight |

## Files
- `case/build_case.py` — parametric model (Python + manifold3d). `python3 case/build_case.py`
  writes print-ready STLs to `case/stl/`. Change a measurement at the top, re-run.
- `case/check_case.py` — fit check: parts vs component stand-ins, closing path, screws, ports,
  printability. Run it after every change, before printing.
- `tools/frame_test.py` — draws a frame on the panel edge pixels to measure the image area.

## v2 (after the trip)
Thinner grip: solder wires to the pin tips (~13 mm thinner, back shell reprint only), or plug
the display onto the Pi and move the buttons to a GPIO splitter or a small USB keypad.
