# Pi-Reader Case Design Specification

## Purpose
This document captures all hardware measurements and design requirements needed to generate a 3D-printable enclosure for the Pi-Reader device. Parked for Phase 2 — resume once software is stable and buttons are wired.

## Hardware Stack (top to bottom)
1. Waveshare 3.7" e-Paper HAT (480×280px, 1-bit)
2. Raspberry Pi Zero 2 WH
3. PiSugar 2 battery HAT

## Measurements needed before designing
Fill these in with calipers before starting OpenSCAD:

| Component | Measurement | Value |
|---|---|---|
| Waveshare HAT PCB | Length × Width | ___ × ___ mm |
| Waveshare HAT PCB | Thickness | ___ mm |
| Display panel active area | Width × Height | ___ × ___ mm |
| Display panel total | Width × Height including bezel | ___ × ___ mm |
| FPC ribbon cable | Length from HAT to panel | ___ mm |
| Pi Zero PCB | Length × Width | 65 × 30 mm (standard) |
| Pi Zero PCB | Thickness | ___ mm |
| PiSugar 2 | Length × Width | ___ × ___ mm |
| PiSugar 2 | Thickness | ___ mm |
| Full stack (Pi + PiSugar) | Total height | ___ mm |
| USB port (PWR IN) | Distance from Pi bottom edge | ___ mm |
| USB port | Width × Height of cutout needed | ___ × ___ mm |
| GPIO header | Height above Pi PCB | ___ mm |

## Button spec
- Type: 6×6×9.5mm tactile momentary push button, through-hole, 4-pin
- Quantity: 4 (up, down, select, back)
- Placement: right side of case (portrait orientation), stacked vertically
- Stem height 9.5mm chosen to protrude through case wall with tactile feel

## Design requirements
- **Orientation**: portrait (display taller than wide)
- **Two-part snap-fit**: front shell (display + buttons) + back lid (battery access)
- **Display window**: cutout matching active area with ~1mm lip to retain panel
- **Button holes**: 4× 7mm diameter circular holes on right edge, evenly spaced
- **USB cutout**: bottom edge, for PiSugar2 charging port
- **Ventilation**: Pi Zero 2 runs warm — consider 3–4 small slots on back
- **Wall thickness**: 2mm minimum for FDM printing strength
- **Material**: PLA or PETG, 0.2mm layer height recommended
- **Aesthetics**: minimal, flush front face, slight chamfer on edges

## Files to generate (when ready)
- `case-front.scad` — display shell with window and button holes
- `case-back.scad` — back lid with snap clips and USB cutout
- `case-assembly.scad` — full assembly preview

## Resume checklist
- [ ] Fill in all measurements above
- [ ] Confirm button GPIO pin assignments
- [ ] Confirm PiSugar2 charging port position
- [ ] Decide final orientation (portrait vs landscape)
- [ ] Generate OpenSCAD files
- [ ] Test print in PLA
- [ ] Iterate on fit
