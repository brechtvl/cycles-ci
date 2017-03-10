
import os

# devices
devices = [
    {'id': 'intel_4790k', 'name': 'Intel i7-4790K', 'os': 'Ubuntu Linux', 'type': 'NONE', 'tile_size': 32, 'sample_factor': 1.0},
    {'id': 'nvidia_gtx1080', 'name': 'NVidia GTX 1080', 'os': 'Ubuntu Linux', 'type': 'CUDA', 'tile_size': 256, 'sample_factor': 1.0},
    {'id': 'amd_rx480', 'name': 'AMD Radeon RX 480', 'os': 'Ubuntu Linux', 'type': 'OPENCL', 'tile_size': 256, 'sample_factor': 1.0},
]

# system configuration commands befor running server
system_config_commands = [
    # prompt once for SSH passphrase
    "ssh-add ~/.ssh/id_rsa",
    # disable turboboost
    "echo \"1\" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo",
    # disable ASLR
    "echo \"0\" | sudo tee /proc/sys/kernel/randomize_va_space"
]

# directories
scripts_dir = os.path.dirname(os.path.realpath(__file__))
ci_dir = os.path.dirname(scripts_dir)

# blender
blender_dir = os.path.join(ci_dir, 'blender')
build_dir = os.path.join(ci_dir, 'build')
blender_exe = os.path.join(build_dir, 'bin', 'blender')

# scenes
scenes_dir = os.path.join(ci_dir, 'scenes')
scenes = {}
for name in os.listdir(scenes_dir):
    filename = os.path.join(scenes_dir, name, name + '.blend')
    if os.path.isfile(filename):
        scenes[name] = filename

# runs
runs = 6
max_runs = 6

# logs
logs_dir = os.path.join(ci_dir, 'logs')

# website
www_dir = os.path.join(ci_dir, 'www')
www_images_dir = os.path.join(www_dir, 'images')
master_json = os.path.join(www_dir, 'master.json')
diffs_json = os.path.join(www_dir, 'diffs.json')
tags_json = os.path.join(www_dir, 'tags.json')

