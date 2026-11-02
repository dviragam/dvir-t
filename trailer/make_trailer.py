"""5-axle semi-trailer (generic flatbed/container chassis) -> STEP.
Units: mm. X = length (front/kingpin at 0, rear at +X), Y = width, Z = up (ground = 0)."""
import cadquery as cq

L, W = 13600, 2550          # overall length / width
DECK_Z = 1500               # top of deck above ground
BEAM_H, BEAM_T = 600, 14    # main I-beam height / web thickness
BEAM_Y = 450                # main beams at +/- BEAM_Y
FLANGE_W, FLANGE_T = 200, 20
AXLE_X0, PITCH, N_AX = 6700, 1400, 5
TRACK = 1840                # wheel-center to wheel-center across axle
TIRE_D, TIRE_W = 1020, 295  # 295/80R22.5
RIM_D = 572
AXLE_Z = TIRE_D / 2

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1-x0, y1-y0, z1-z0, centered=False).translate((x0, y0, z0))

def ibeam(y):
    z0 = DECK_Z - 50 - BEAM_H
    web = box(0, L-200, y-BEAM_T/2, y+BEAM_T/2, z0, z0+BEAM_H)
    top = box(0, L-200, y-FLANGE_W/2, y+FLANGE_W/2, z0+BEAM_H-FLANGE_T, z0+BEAM_H)
    bot = box(0, L-200, y-FLANGE_W/2, y+FLANGE_W/2, z0, z0+FLANGE_T)
    return web.union(top).union(bot)

parts = {}   # name -> (shape, color)

# --- frame ---
frame = ibeam(BEAM_Y).union(ibeam(-BEAM_Y))
zb = DECK_Z - 50 - BEAM_H
for i, x in enumerate(range(900, L-300, 1000)):          # cross members
    frame = frame.union(box(x, x+80, -W/2+100, W/2-100, zb+BEAM_H-140, zb+BEAM_H-50))
frame = frame.union(box(0, 1700, -BEAM_Y-120, BEAM_Y+120, zb+BEAM_H-60, zb+BEAM_H))  # gooseneck plate
frame = frame.union(box(L-300, L-200, -W/2+100, W/2-100, zb, zb+BEAM_H))             # rear cross beam
parts["frame"] = (frame, (0.15, 0.25, 0.55))

# --- deck (flatbed floor) ---
deck = box(1700, L, -W/2, W/2, DECK_Z-50, DECK_Z).union(box(0, 1700, -W/2+300, W/2-300, DECK_Z-50, DECK_Z))
parts["deck"] = (deck, (0.55, 0.45, 0.30))

# --- kingpin (2") + king pin plate ---
kp = (cq.Workplane("XY").workplane(offset=DECK_Z-250).center(1550, 0).circle(25.4*2/2*1.0).extrude(250)
      .union(cq.Workplane("XY").workplane(offset=DECK_Z-250).center(1550, 0).circle(75).extrude(20)))
parts["kingpin"] = (kp, (0.6, 0.6, 0.6))

# --- landing gear ---
LX = 4000
leg = cq.Workplane("XY")
for s in (1, -1):
    y = s*(BEAM_Y+260)
    leg = leg.union(box(LX-60, LX+60, y-60, y+60, 380, zb+BEAM_H-60))
    leg = leg.union(box(LX-200, LX+200, y-120, y+120, 340, 380))
leg = leg.union(box(LX-60, LX+60, -BEAM_Y-260, BEAM_Y+260, zb+BEAM_H-200, zb+BEAM_H-120))
parts["landing_gear"] = (leg, (0.9, 0.7, 0.1))

# --- container twist-locks (40 ft) ---
tl = cq.Workplane("XY")
for x in (1100, 1100+ (L-1100-400)):
    for y in (-1118, 1118):
        tl = tl.union(cq.Workplane("XY").workplane(offset=DECK_Z).center(x, y).rect(160, 120).extrude(40))
parts["twistlocks"] = (tl, (0.7, 0.7, 0.7))

# --- axles / suspension / wheels ---
def wheel():
    tire = (cq.Workplane("XZ").circle(TIRE_D/2).circle(RIM_D/2).extrude(TIRE_W/2, both=True)
            .edges().fillet(25))
    rim = (cq.Workplane("XZ").circle(RIM_D/2).circle(120).extrude(TIRE_W*0.35, both=True))
    hub = cq.Workplane("XZ").circle(110).extrude(TIRE_W*0.55, both=True)
    return tire, rim.union(hub)

tire0, rim0 = wheel()
tires = cq.Workplane("XY"); rims = cq.Workplane("XY")
axles = cq.Workplane("XY"); susp = cq.Workplane("XY")
for i in range(N_AX):
    x = AXLE_X0 + i*PITCH
    axles = axles.union(box(x-75, x+75, -TRACK/2, TRACK/2, AXLE_Z-75, AXLE_Z+75))
    for s in (1, -1):
        yc = s*TRACK/2
        for dy in (-175, 175):   # dual wheels
            tires = tires.union(tire0.translate((x, yc+dy, AXLE_Z)))
            rims = rims.union(rim0.translate((x, yc+dy, AXLE_Z)))
        # leaf spring + hangers + spring seat
        ys = s*(BEAM_Y+0)  # springs under the main beams
        ys = s*(TRACK/2-300)
        susp = susp.union(box(x-550, x+550, ys-45, ys+45, AXLE_Z+75, AXLE_Z+75+80))
        susp = susp.union(box(x-120, x+120, ys-60, ys+60, AXLE_Z+155, zb-0))
    # brake chambers (simple cylinders)
parts["tires"] = (tires, (0.05, 0.05, 0.05))
parts["rims"] = (rims, (0.8, 0.8, 0.8))
parts["axles"] = (axles, (0.3, 0.3, 0.3))
parts["suspension"] = (susp, (0.25, 0.25, 0.25))

# --- rear bumper + lights bar ---
bump = box(L-200, L-120, -W/2+200, W/2-200, 650, 850)
parts["rear_bumper"] = (bump, (0.7, 0.1, 0.1))

asm = cq.Assembly(name="trailer_5_axle")
for n, (shp, c) in parts.items():
    asm.add(shp, name=n, color=cq.Color(*c))
out = "/home/user/dvir-t/trailer/trailer_5_axle.step"
asm.save(out, 'STEP')
print("saved", out)
