
import bpy
import math
import os
import sys

argv = sys.argv[sys.argv.index("--") + 1:]
device_type = argv[0]
tile_size = int(argv[1])
sample_factor = float(argv[2])

prefs = bpy.context.preferences
scene = bpy.context.scene

try:
    if hasattr(prefs.system, 'compute_device_type'):
        prefs.system.compute_device_type = device_type
    else:
        cprefs = prefs.addons['cycles'].preferences
        cprefs.compute_device_type = device_type
        for device in cprefs.devices:
            if device.type == device_type:
                device.use = device.type == device_type
except:
    print("Cycles device not available")
    sys.exit(1)

scene.render.tile_x = tile_size
scene.render.tile_y = tile_size

if device_type == 'NONE':
    scene.cycles.device = 'CPU'
else:
    scene.cycles.device = 'GPU'

def adjust_samples(samples):
    new_samples = samples * sample_factor
    return max(1, int(new_samples + 0.5))

scene.cycles.samples = adjust_samples(scene.cycles.samples)
scene.cycles.aa_samples = adjust_samples(scene.cycles.aa_samples)

