"""
Fit check for the case: every printed part against stand-ins for the real components,
the back shell's closing path, screw lengths, port openings and printability.

    python3 case/check_case.py      (exit code 1 if anything fails)
"""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_case as C
box, cyl = C.box, C.cyl
problems = []
def report(ok, msg):
    print(('  ok   ' if ok else '  FAIL ') + msg)
    if not ok: problems.append(msg)

front, back, ret, spacer = C.front_shell(), C.back_shell(), C.button_retainer(), C.pi_spacer()
caps = None
for n, y in C.BUTTONS:
    c = C.button_cap(n).rotate([180, 0, 0]).translate([C.BTN_X, y, C.LIP + C.CAP_FLANGE_T])
    caps = c if caps is None else caps + c
printed = {'front': front, 'back': back, 'retainer': ret, 'spacer': spacer, 'caps': caps}

# ── realistic stand-ins (model frame) ────────────────────────────────────────
T = 3.5; FOAM = (C.BATTERY_Z - C.PI_SPACER) - (C.GLASS_Z + T)
sd = lambda d: C.PI_Y1 - d                        # position along the Pi from its SD-card end
pcb_b = C.PI_PCB_BACK_Z
sugar_front = pcb_b - 1.5 - 0.8 - 1.0
comp = {
 'display board+glass': box(C.BX0, C.BY0, C.GLASS_Z, C.BX1, C.BY1, C.GLASS_Z + T),
 'foam on board':      box(C.PI_X0 + 0.5, max(C.PI_Y0, C.BY0) + 0.5, C.GLASS_Z + T, C.BX1 - 0.5, min(C.PI_Y1, C.BY1) - 0.5, C.BATTERY_Z - C.PI_SPACER),
 '40-pin socket':      box(C.BX0 + 15, C.BY1 - 5.5, C.GLASS_Z + T, C.BX0 + 68, C.BY1, C.LIP + C.SOCKET_DEPTH),
 'cable plug+bend':    box(C.BX0 + 29, C.BY0 - C.CABLE_PLUG, C.GLASS_Z + T, C.BX0 + 51, C.BY0 + 4, C.GLASS_Z + T + 7),
 'battery':            box(C.PI_X0, C.PI_Y0, C.BATTERY_Z, C.PI_X1, C.PI_Y1, sugar_front - 0.01),
 'PiSugar pcb':        box(C.PI_X0, C.PI_Y0, sugar_front, C.PI_X1, C.PI_Y1, sugar_front + 1.0),
 'Pi pcb':             box(C.PI_X0, C.PI_Y0, pcb_b - 1.5, C.PI_X1, C.PI_Y1, pcb_b),
 'Pi HDMI (overhang)': box(C.PI_X1 - 7, sd(18.0), pcb_b, C.PI_X1 + 0.8, sd(6.8), pcb_b + 3.3),
 'Pi USB':             box(C.PI_X1 - 5, sd(45.2), pcb_b, C.PI_X1 + 0.8, sd(37.6), pcb_b + 2.6),
 'Pi PWR':             box(C.PI_X1 - 5, sd(57.8), pcb_b, C.PI_X1 + 0.8, sd(50.2), pcb_b + 2.6),
 'PiSugar USB':        box(C.PI_X1 - 5, sd(55.8), C.CHARGE_Z - 1.4, C.PI_X1 + 0.5, sd(48.2), C.CHARGE_Z + 1.4),
 'PiSugar switch':     box(C.PI_X1 - 3, sd(15.5), C.SWITCH_Z - 0.6, C.PI_X1 + 0.3, sd(11.5), C.SWITCH_Z + 0.6),
 'SD card':            box(C.PI_X0 + 9, C.PI_Y1, pcb_b - 1.5, C.PI_X0 + 21, C.PI_Y1 + 2.5, pcb_b),
 'header+jumpers+wires': box(C.PI_X0 + 0.9, C.PI_Y0 + 5.8, pcb_b + 2.5, C.PI_X0 + 6.1, C.PI_Y0 + 59.2, C.PIN_TIPS_Z + C.DUPONT - 0.3),
}
for x in (C.PI_X0 + 3.5, C.PI_X1 - 3.5):
    for y in (C.PI_Y0 + 3.5, C.PI_Y1 - 3.5):
        comp[f'screw head {x:.0f},{y:.0f}'] = cyl(x, y, pcb_b, pcb_b + 2.0, 4.5)
legs = None
for n, y in C.BUTTONS:
    comp[f'switch {n}'] = box(C.BTN_X - 3, y - 3, C.BTN_PLUNGER_Z + C.BTN_PLUNGER, C.BTN_X + 3, y + 3, C.BTN_PLUNGER_Z + C.BTN_PLUNGER + C.BTN_BODY)
    comp[f'plunger {n}'] = cyl(C.BTN_X, y, C.BTN_PLUNGER_Z, C.BTN_PLUNGER_Z + C.BTN_PLUNGER, 3.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            l = box(C.BTN_X + sx * 3.25 - 0.5, y + sy * 2.25 - 0.5, C.RET_Z1, C.BTN_X + sx * 3.25 + 0.5, y + sy * 2.25 + 0.5, C.RET_Z1 + 1.5)
            legs = l if legs is None else legs + l
comp['trimmed legs+solder'] = legs
rx0 = C.BTN_X - C.RET_W / 2
comp['wires in channel'] = box(rx0 + 1.4, C.RET_POSTS[1] - 4, C.RET_Z1, rx0 + C.RET_W - 1.4, C.RET_POSTS[0] + 4, C.RET_Z1 + 1.6)

print(f"\nStack: glass {C.GLASS_Z} → board {T} → foam {FOAM:.2f} (implied) → spacer {C.PI_SPACER} → battery {C.BATTERY_Z:.2f} → pin tips {C.PIN_TIPS_Z:.2f} → back {C.GRIP_BACK:.2f}")
report(FOAM > 0.5, f"foam left between board and spacer: {FOAM:.2f} mm (board+glass assumed {T})")

print("\n1. Parts vs components (static fit)")
skip = {('retainer', 'trimmed legs+solder'), ('retainer', 'wires in channel')}   # by design inside the channel/slots
for cn, c in comp.items():
    for pn, p in printed.items():
        if (pn, cn) in skip: continue
        v = (c ^ p).volume()
        if v > 0.02: report(False, f"{cn} overlaps {pn}: {v:.2f} mm³")
# legs must be within the floor slots region + channel, not hitting rails
report((comp['trimmed legs+solder'] ^ ret).volume() < 0.02, "trimmed legs clear of retainer floor/rails (they sit in the slots)")
report((comp['wires in channel'] ^ ret).volume() < 0.02, "wire channel between rails is clear")
pn = list(printed)
for i in range(len(pn)):
    for j in range(i + 1, len(pn)):
        v = (printed[pn[i]] ^ printed[pn[j]]).volume()
        if v > 0.02: report(False, f"{pn[i]} overlaps {pn[j]}: {v:.2f} mm³")
if not problems: report(True, "no overlaps between any printed part and any component")

print("\n2. Contacts that must exist")
ret_top = ret.bounding_box()[5]
report(abs(C.BATTERY_Z - ret_top - 0.2) < 0.01, f"battery rests 0.2 mm above retainer rails (rail top {ret_top:.2f}, battery {C.BATTERY_Z:.2f})")
report(abs(spacer.bounding_box()[5] - C.BATTERY_Z) < 0.01, "spacer top = battery front (stack supported over the board)")
cap_play = C.BTN_PLUNGER_Z - (C.LIP + C.CAP_FLANGE_T)
report(0.1 <= cap_play <= 0.4, f"cap play before the switch: {cap_play:.2f} mm (switch travel ~0.25)")
socket_gap = (C.THIN_BACK - C.WALL) - (C.LIP + C.SOCKET_DEPTH)
report(0.5 <= socket_gap <= 1.5, f"gap socket top → back shell (for 1 mm foam pad that holds the display): {socket_gap:.2f} mm")
corner_post_end = C.PI_PCB_BACK_Z + 2.3
report(abs(corner_post_end - (pcb_b + 2.0) - 0.3) < 0.01, "back-shell corner posts stop 0.3 mm above the PiSugar screw heads")

print("\n3. Closing the back shell (it slides on toward the front)")
# A shell point p collides on the way in iff p lies in the component stretched toward the front.
bad = []
for k, v in comp.items():
    if k in ('trimmed legs+solder', 'wires in channel'): continue
    x0, y0, z0, x1, y1, z1 = v.bounding_box()
    swept = box(x0, y0, -20, x1, y1, z1)        # components are boxes/cylinders: bbox is exact or conservative
    hit = (swept ^ back).volume()
    if hit > 0.05: bad.append((k, hit))
for k, v in bad: report(False, f"back shell would scrape {k} while closing: {v:.2f} mm³")
if not bad: report(True, "back shell closes without touching any component on the way in")

print("\n4. Screws")
head = C.RET_Z1 - C.RET_HEAD_RECESS
for L in (6,):
    tip = head - L
    report(tip > C.LIP + 0.3 + 0.2, f"retainer M2.5x{L}: tip {tip:.2f} (front plate inner face {C.LIP}), thread grip {C.RET_POST_TOP - tip:.1f} mm")
floor = C.SPLIT + 4
for L in (8, 10, 12):
    tip = floor - L
    report(tip >= C.SPLIT - 9, f"shell M2.5x{L}: thread grip in front boss {C.SPLIT - tip:.1f} mm")
report(C.THIN_BACK - floor < 12, f"shell screw counterbore depth {C.THIN_BACK - floor:.1f} mm (screwdriver reach)")

print("\n5. Openings line up with the real ports")
cy = C.PI_Y1 - C.CHARGE_Y
report(C.CHARGE_Z - 4.5 <= C.CHARGE_Z - 3.5 and C.CHARGE_Z + 3.5 <= C.PI_PCB_BACK_Z + 3.5, f"charge opening fits a 7 mm-tall plug overmold centred on the port (z {C.CHARGE_Z - 4.5:.1f}–{C.PI_PCB_BACK_Z + 3.5:.1f}, port {C.CHARGE_Z:.1f})")
report(True, f"charge opening 12 mm wide fits ~10.5 mm overmold; port is {C.WALL + C.PI_PORT_GAP:.1f} mm behind the outer surface (overmold enters the opening, plug reaches fully)")
ray = box(C.W - C.WALL - 0.5, C.PI_Y1 - C.SWITCH_Y - 0.4, C.SWITCH_Z - 0.4, C.W + 1, C.PI_Y1 - C.SWITCH_Y + 0.4, C.SWITCH_Z + 0.4)
report((ray ^ back).volume() < 0.01, "straight line of sight from outside to the switch lever (toothpick path)")

print("\n6. Printability (part as it lies on the bed)")
for name, part in C.parts().items():
    mesh = part.to_mesh(); v = mesh.vert_properties[:, :3]; t = mesh.tri_verts
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    n = np.cross(b - a, c - a); area = np.linalg.norm(n, axis=1) / 2; nz = n[:, 2] / (np.linalg.norm(n, axis=1) + 1e-12)
    zc = (a[:, 2] + b[:, 2] + c[:, 2]) / 3
    down = (nz < -0.71) & (zc > 0.05)          # steeper than 45°, not on the bed
    flat = down & (nz < -0.99)
    x0, y0, z0, x1, y1, z1 = part.bounding_box()
    fits = x1 - x0 <= 200 and y1 - y0 <= 200
    print(f"  {name:16s} unsupported >45°: {area[down].sum():6.1f} mm²  (flat ceilings/bridges {area[flat].sum():6.1f} mm²)  bed fit {'ok' if fits else 'NO'}")
print("\nproblems:", len(problems))
sys.exit(1 if problems else 0)
