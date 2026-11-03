"""
Parametric case for the Pi-Reader. Writes printable STLs to case/stl/.

    pip install manifold3d numpy
    python3 case/build_case.py

Coordinates (mm), front view as held in the right hand:
    x  left → right (button wing on the right)
    y  bottom → top (display cable plug in the bottom "chin")
    z  front face (0) → back
With z pointing away from the viewer this frame is a mirror image, so every part is
mirrored in x on export (see parts()).
Layout and measurements: docs/case-design-spec.md
"""
import os
import struct
from functools import reduce

import manifold3d as m3d

# ── Measured ─────────────────────────────────────────────────────────────────
BOARD_W, BOARD_H = 101.7, 63.1   # display board outline
SOCKET_DEPTH = 22.0              # glass front → top of the unused 40-pin socket
STACK_DEPTH = 37.11              # glass front → Pi header pin tips, Pi stack lying on foam
PI_STACK = 30.62                 # Pi + PiSugar + battery alone: battery front → pin tips
CABLE_PLUG = 14.7                # display cable plug + bend, below the board's bottom edge
# Along the Pi from its SD-card end, and depth in front of the Pi PCB's back face
# (read off a side photo scaled by the 65 mm Pi)
CHARGE_Y = 52.0          # PiSugar charge port centre (port ends at 55.8)
CHARGE_DZ = 4.4
SWITCH_Y = 13.6          # PiSugar slide switch lever; ON is toward the SD-card end
SWITCH_DZ = 4.1

# tools/frame_test.py: board edge → outer frame line, front view (ribbon left, plug bottom)
IMG_LEFT, IMG_RIGHT, IMG_BOTTOM, IMG_TOP = 14.21, 10.62, 10.10, 11.12

# ── Estimated ────────────────────────────────────────────────────────────────
# The measured image (76.9 × 41.9) isn't 480:280, so trust its centre, not its size:
# the window is the datasheet image area centred there, which can't clip any pixels.
ACTIVE_W, ACTIVE_H = 81.12, 47.32
WINDOW_X0 = IMG_LEFT + (BOARD_W - IMG_LEFT - IMG_RIGHT) / 2 - ACTIVE_W / 2
WINDOW_Y0 = IMG_BOTTOM + (BOARD_H - IMG_BOTTOM - IMG_TOP) / 2 - ACTIVE_H / 2
PI_ABOVE_BOARD = 1.7     # Pi PCB (SD-card end) past the board's top edge
WIRES_ON_PINS = 4.0      # wires soldered to the pin tips and bent flat (jumper plugs need 37)

# ── Design ───────────────────────────────────────────────────────────────────
WALL = 2.0
LIP = 1.6                # front plate thickness over the glass
R = 4.0                  # outer corner radius
LEFT_GAP = 2.0           # display ribbon wraps around the board's left edge
TOP_GAP = 6.0            # SD card + screw bosses
CHIN = CABLE_PLUG + 0.3
WING = 18.0              # button column
SPLIT = 12.0             # front/back shell joint
PI_W, PI_L = 30.0, 65.0
PI_PORT_GAP = 1.5        # Pi connectors overhang the PCB edge slightly
# Printed plate under the Pi stack (on top of the existing foam). Without it the battery,
# which overhangs the button wing, would sit on the button retainer.
PI_SPACER = 5.0

BTN_PITCH = 14.0
# Tall 6×6 tactile switches (9.96 mm measured): the plunger itself pokes through the front
BTN_TOTAL, BTN_BODY = 9.96, 3.5
BTN_PLUNGER = BTN_TOTAL - BTN_BODY
PLUNGER_HOLE = 4.2       # round 3.5 mm plunger
PLUNGER_PROUD = 1.0
BTN_LEG_PITCH = 6.5
SCREW_PILOT, SCREW_CLEAR, SCREW_HEAD = 2.2, 2.9, 5.6   # M2.5 self-tapping
FN = 48

# ── Derived ──────────────────────────────────────────────────────────────────
BX0, BY0 = WALL + LEFT_GAP, WALL + CHIN          # board lower-left
BX1, BY1 = BX0 + BOARD_W, BY0 + BOARD_H
W = BX1 + WING + WALL
H = BY1 + TOP_GAP + WALL
GLASS_Z = LIP
PIN_TIPS_Z = LIP + STACK_DEPTH + PI_SPACER
BATTERY_Z = PIN_TIPS_Z - PI_STACK                 # battery's front face
THIN_BACK = LIP + SOCKET_DEPTH + 1.0 + WALL       # 1 mm foam pad on the socket
GRIP_BACK = PIN_TIPS_Z + WIRES_ON_PINS + WALL
PI_X1 = W - WALL - PI_PORT_GAP                    # port side
PI_X0 = PI_X1 - PI_W
PI_Y1 = BY1 + PI_ABOVE_BOARD                      # SD-card end
PI_Y0 = PI_Y1 - PI_L
PI_PCB_BACK_Z = PIN_TIPS_Z - 8.5
CHARGE_Z = PI_PCB_BACK_Z - CHARGE_DZ
SWITCH_Z = PI_PCB_BACK_Z - SWITCH_DZ
GRIP_X0 = PI_X0 - 6.0
RAMP = GRIP_BACK - THIN_BACK

BTN_X = BX1 + WING / 2
BTN_MID_Y = (BY0 + BY1) / 2
# top → bottom: Back, Up, Down, Select
BUTTONS = [('back', BTN_MID_Y + 1.5 * BTN_PITCH), ('up', BTN_MID_Y + 0.5 * BTN_PITCH),
           ('down', BTN_MID_Y - 0.5 * BTN_PITCH), ('select', BTN_MID_Y - 1.5 * BTN_PITCH)]
BTN_PLUNGER_Z = -PLUNGER_PROUD                      # plunger tip, in front of the case face
RET_Z0 = BTN_PLUNGER_Z + BTN_PLUNGER                # retainer front face = switch body front
RET_FLOOR = 1.2
RET_Z1 = RET_Z0 + BTN_BODY + RET_FLOOR
RET_W = 12.0
RET_POSTS = [BUTTONS[0][1] + 10, BUTTONS[-1][1] - 10]
RET_POST_TOP = RET_Z1 - 2.0      # posts rise into the retainer so an M2.5×6 bites ~5 mm
RET_HEAD_RECESS = 0.8

BOSSES = [(10, WALL + 3.5), (70, WALL + 3.5), (10, H - WALL - 3.0), (75, H - WALL - 3.0)]


def box(x0, y0, z0, x1, y1, z1):
    return m3d.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(x, y, z0, z1, d):
    return m3d.Manifold.cylinder(z1 - z0, d / 2, d / 2, FN).translate([x, y, z0])


def rounded(x0, y0, x1, y1, z0, z1, r):
    pts = [(x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)]
    cs = m3d.CrossSection.batch_hull([m3d.CrossSection.circle(r, FN).translate(p) for p in pts])
    return m3d.Manifold.extrude(cs, z1 - z0).translate([0, 0, z0])


def union(parts):
    return reduce(lambda a, b: a + b, parts)


def polygon(points, h):
    return m3d.Manifold.extrude(m3d.CrossSection([points]), h)


# ── Parts ────────────────────────────────────────────────────────────────────

def front_shell():
    shell = rounded(0, 0, W, H, 0, SPLIT, R) - rounded(WALL, WALL, W - WALL, H - WALL, LIP, SPLIT + 1, R - WALL)

    # window bevelled 45° outward so the frame doesn't shade the image edge
    wx0, wy0 = BX0 + WINDOW_X0 - 0.5, BY0 + WINDOW_Y0 - 0.5
    wx1, wy1 = wx0 + ACTIVE_W + 1.0, wy0 + ACTIVE_H + 1.0
    window = (box(wx0, wy0, LIP - 0.01, wx1, wy1, LIP + 1)
              + box(wx0 - LIP, wy0 - LIP, -1, wx1 + LIP, wy1 + LIP, -0.99)).hull()
    shell -= window

    for _, y in BUTTONS:
        shell -= cyl(BTN_X, y, -1, LIP + 1, PLUNGER_HOLE)

    # L-shaped locators at the board corners
    t, leg, hgt, c = 1.2, 6.0, 3.0, 0.3
    for cx, sx in ((BX0 - c, -1), (BX1 + c, 1)):
        for cy, sy in ((BY0 - c, -1), (BY1 + c, 1)):
            xa, xb = sorted((cx, cx + sx * t))
            ya, yb = sorted((cy, cy - sy * leg))
            shell += box(xa, ya, LIP, xb, yb, LIP + hgt)
            xa, xb = sorted((cx, cx - sx * leg))
            ya, yb = sorted((cy, cy + sy * t))
            shell += box(xa, ya, LIP, xb, yb, LIP + hgt)

    for x, y in BOSSES:
        shell += cyl(x, y, LIP, SPLIT, 6.0)
        shell -= cyl(x, y, SPLIT - 9, SPLIT + 1, SCREW_PILOT)

    for y in RET_POSTS:
        shell += cyl(BTN_X, y, LIP, RET_POST_TOP, 6.0)
        shell -= cyl(BTN_X, y, LIP + 0.3, RET_POST_TOP + 1, SCREW_PILOT)
    return shell


def back_shell():
    def body(inset, z0):
        x0, y0, x1, y1 = inset, inset, W - inset, H - inset
        r = max(R - inset, 0.5)
        thin = rounded(x0, y0, x1, y1, z0, THIN_BACK - inset, r)
        # inner ramp shifted along x as well, so the 45° wall keeps ~WALL normal thickness
        dx = 0.8 if inset else 0
        grip = (rounded(GRIP_X0 + dx, y0, x1, y1, z0, GRIP_BACK - inset, r)
                + rounded(GRIP_X0 - RAMP + dx, y0, GRIP_X0 + dx + 1, y1, z0, THIN_BACK - inset, r)).hull()
        return thin + grip

    shell = body(0, SPLIT) - body(WALL, SPLIT - 1)

    # skirt that slides inside the front shell walls
    skirt_out = rounded(WALL + 0.3, WALL + 0.3, W - WALL - 0.3, H - WALL - 0.3, SPLIT - 2, SPLIT + 0.01, R - WALL)
    skirt_in = rounded(WALL + 1.4, WALL + 1.4, W - WALL - 1.4, H - WALL - 1.4, SPLIT - 3, SPLIT + 1, 1)
    shell += skirt_out - skirt_in
    shell -= box(BX0 + 27, 0, SPLIT - 3, BX0 + 53, WALL + 2, SPLIT + 0.5)   # display cable plug
    # Pi connectors overhang the PCB edge; the rim would drag across them while closing
    shell -= box(PI_X1 - 1, PI_Y0 - 3, SPLIT - 3, W - WALL + 0.01, PI_Y1 + 3, SPLIT + 0.5)
    for x, y in BOSSES:
        shell -= cyl(x, y, SPLIT - 3, SPLIT + 1, 7.0)   # clear the front bosses

    inner_back = THIN_BACK - WALL
    for x, y in BOSSES:
        shell += cyl(x, y, SPLIT, inner_back, 6.0)
        shell -= cyl(x, y, SPLIT - 1, THIN_BACK + 1, SCREW_CLEAR)
        shell -= cyl(x, y, SPLIT + 4, THIN_BACK + 1, SCREW_HEAD)

    # Pi stack: posts onto the PiSugar screw heads at the Pi corners, stops at both ends
    grip_inner = GRIP_BACK - WALL
    for x in (PI_X0 + 3.5, PI_X1 - 3.5):
        for y in (PI_Y0 + 3.5, PI_Y1 - 3.5):
            shell += cyl(x, y, PI_PCB_BACK_Z + 2.3, grip_inner + 0.5, 4.0)
    shell += box(PI_X0 + 8, PI_Y0 - 1.3, PI_PCB_BACK_Z - 2, PI_X1, PI_Y0 - 0.3, grip_inner + 0.5)
    shell += box(PI_X1 - 6, PI_Y1 + 0.3, PI_PCB_BACK_Z - 2, PI_X1, PI_Y1 + 1.3, grip_inner + 0.5)
    # keep the port side 1.5 mm off the wall; full height so they print without overhang
    for y in (PI_Y1 - 30, PI_Y1 - 4):
        shell += box(PI_X1, y - 1.5, PI_PCB_BACK_Z - 1.4, W - WALL + 0.1, y + 1.5, grip_inner + 0.5)

    # right wall: charge opening (also exposes the Pi's PWR IN), and a slot to flick the
    # PiSugar switch with a toothpick — a slider would scrape the PCB edge while closing
    cy = PI_Y1 - CHARGE_Y
    shell -= box(W - WALL - 1, cy - 6, CHARGE_Z - 4.5, W + 1, cy + 6, PI_PCB_BACK_Z + 3.5)
    sy = PI_Y1 - SWITCH_Y
    shell -= box(W - WALL - 1, sy - 3.5, SWITCH_Z - 1.8, W + 1, sy + 3.5, SWITCH_Z + 1.8)

    for i in range(4):
        x = PI_X0 + 9 + i * 5
        shell -= box(x, PI_Y0 + 18, GRIP_BACK - WALL - 1, x + 2, PI_Y1 - 18, GRIP_BACK + 1)
    return shell


def button_retainer():
    """Holds the 4 switches like a PCB: legs poke through the floor and get soldered there.
    The two rails on the back carry the overhanging battery; wires run between them."""
    y0, y1 = RET_POSTS[1] - 4, RET_POSTS[0] + 4
    x0 = BTN_X - RET_W / 2
    part = box(x0, y0, RET_Z0, x0 + RET_W, y1, RET_Z1)
    for rx in (x0, x0 + RET_W - 1.2):
        part += box(rx, y0, RET_Z1 - 0.01, rx + 1.2, y1, BATTERY_Z - 0.2)
    for _, y in BUTTONS:
        part -= box(BTN_X - 3.6, y - 3.15, RET_Z0 - 1, BTN_X + 3.6, y + 3.15, RET_Z1 - RET_FLOOR)
        for sx in (-1, 1):
            lx = BTN_X + sx * BTN_LEG_PITCH / 2
            part -= box(lx - 0.7, y - 2.95, RET_Z0 - 1, lx + 0.7, y + 2.95, RET_Z1 + 1)
    for y in RET_POSTS:
        part -= cyl(BTN_X, y, RET_Z0 - 1, RET_POST_TOP, 6.4)   # post top carries the load
        part -= cyl(BTN_X, y, RET_Z0 - 1, RET_Z1 + 1, SCREW_CLEAR)
        part -= cyl(BTN_X, y, RET_Z1 - RET_HEAD_RECESS, RET_Z1 + 1, SCREW_HEAD)
    return part


def pi_spacer():
    """Sits between the foam on the display board and the battery, over the board only."""
    x0, x1 = PI_X0 + 0.5, BX1 - 0.5
    y0, y1 = max(PI_Y0, BY0) + 0.5, min(PI_Y1, BY1) - 0.5
    return rounded(x0, y0, x1, y1, BATTERY_Z - PI_SPACER, BATTERY_Z, 1.5)


# ── Output ───────────────────────────────────────────────────────────────────

def for_printing(part, flip=False):
    """Lay the part flat on the bed (z = 0), optionally upside down."""
    if flip:
        part = part.rotate([180, 0, 0])
    (x0, y0, z0, _, _, _) = part.bounding_box()
    return part.translate([-x0, -y0, -z0])


def write_stl(part, path):
    mesh = part.to_mesh()
    verts, tris = mesh.vert_properties[:, :3], mesh.tri_verts
    with open(path, 'wb') as f:
        f.write(b'pi-reader'.ljust(80, b' '))
        f.write(struct.pack('<I', len(tris)))
        for a, b, c in tris:
            va, vb, vc = verts[a], verts[b], verts[c]
            n = [(vb[1] - va[1]) * (vc[2] - va[2]) - (vb[2] - va[2]) * (vc[1] - va[1]),
                 (vb[2] - va[2]) * (vc[0] - va[0]) - (vb[0] - va[0]) * (vc[2] - va[2]),
                 (vb[0] - va[0]) * (vc[1] - va[1]) - (vb[1] - va[1]) * (vc[0] - va[0])]
            f.write(struct.pack('<12fH', *n, *va, *vb, *vc, 0))


def parts():
    def real(part):
        return part.mirror([1, 0, 0])

    out = {
        'front_shell': for_printing(real(front_shell())),
        'back_shell': for_printing(real(back_shell()), flip=True),
        'button_retainer': for_printing(real(button_retainer())),   # front face down
        'pi_spacer': for_printing(real(pi_spacer())),
    }
    return out


if __name__ == '__main__':
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stl')
    os.makedirs(out_dir, exist_ok=True)
    print(f"Case outside: {W:.1f} × {H:.1f} mm, {THIN_BACK:.1f} mm thin / {GRIP_BACK:.1f} mm grip")
    for name, part in parts().items():
        if part.is_empty() or part.status() != m3d.Error.NoError:
            raise SystemExit(f"{name} is empty or invalid — check the parameters")
        write_stl(part, os.path.join(out_dir, name + '.stl'))
        x0, y0, z0, x1, y1, z1 = part.bounding_box()
        print(f"  {name:16s} {x1 - x0:6.1f} × {y1 - y0:6.1f} × {z1 - z0:5.1f} mm")
