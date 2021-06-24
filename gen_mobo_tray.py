from fnmatch import translate
from solid import scad_render_to_file
from solid.objects import circle, polygon, offset, square, translate

import json

# User definable variables
desired_layouts = ["MiniITX", "MicroATX", "ATX"]
screw_size_diam_mm = 3
cpu_cutout_size = [140, 140]
cpu_cutout_location = [85.09, 85]
cpu_cutout_rounding_radius = 15
circle_segments = 64

###########################################################
# Layout definitions


class Vec2D():
    x: float = 0
    y: float = 0

    def __init__(self, l):
        self.x = l[0]
        self.y = l[1]

    def __str__(self):
        return(f"({self.x}mm, {self.y}mm)")

    def __repr__(self):
        return(f"({self.x}mm, {self.y}mm)")


class MotherboardLayout():
    size: Vec2D
    # Hole locations are in mm from the top right of the motherboard (the corner with the rear panel IO)
    holes: list[Vec2D]

    def __init__(self, dict):
        self.holes = list()
        self.size = Vec2D(dict["size"])
        for hole in dict["holes"]:
            self.holes.append(Vec2D(hole))

    def __str__(self):
        return (f"size: {self.size}, holes: {self.holes}")

    def __repr__(self):
        return (f"size: {self.size}, holes: {self.holes}")


def load_defs(file_path):
    layouts: dict[str, MotherboardLayout] = dict()
    with open(file_path, 'r') as f:
        res = json.load(f)
        for layout_name, layout_data in res.items():
            layouts[layout_name] = MotherboardLayout(layout_data)

    return layouts

#######################################################
# Dimension calculations


class TrayLayout():
    size: Vec2D = Vec2D([0, 0])
    holes: set[Vec2D] = {}

    def gen_openscad(self):
        cutout_offset = self.to_scad_coord_system(Vec2D(cpu_cutout_location))
        cpu_cutout_poly = translate([cutout_offset.x, cutout_offset.y, 0])(
            cpu_cutout(cpu_cutout_size))
        holes = []
        for hole in self.holes:
            pos = self.to_scad_coord_system(hole)
            holes.append(
                translate([pos.x, pos.y, 0])(
                    screw_hole(screw_size_diam_mm)
                )
            )
        res = square([self.size.x, self.size.y])
        res -= cpu_cutout_poly
        for hole in holes:
            res -= hole
        return res

    def to_scad_coord_system(self, vec: Vec2D):
        x = self.size.x - vec.x
        y = self.size.y - vec.y
        return Vec2D([x, y])


def calculate_tray_layout(layout_defs: dict[str, MotherboardLayout], supported_layouts: list[str]):
    size = Vec2D([0, 0])
    holes: set[Vec2D] = set()
    for layout in supported_layouts:
        # Enlarge desired size if current board does not fit
        data = layout_defs[layout]
        if data.size.x > size.x:
            size.x = data.size.x
        if data.size.y > size.y:
            size.y = data.size.y
        # Add any new holes
        for screw in data.holes:
            holes.add(screw)

    # Create final layout
    layout = TrayLayout()
    layout.size = size
    layout.holes = holes
    return layout

#######################################################
# Shape defitinitions


def screw_hole(diam):
    return circle(d=diam)


def cpu_cutout(size):
    base_shape = square(cpu_cutout_size, center=True)
    shrunk = offset(r=-cpu_cutout_rounding_radius)(base_shape)
    return offset(r=cpu_cutout_rounding_radius)(shrunk)


if __name__ == "__main__":
    path = "./tray.scad"
    layouts = load_defs("./motherboard_layouts.json")
    tgt = calculate_tray_layout(layouts, desired_layouts)
    scad = tgt.gen_openscad()

    scad_render_to_file(
        scad, filepath=path, file_header=f'$fn = {circle_segments};', include_orig_code=True)
