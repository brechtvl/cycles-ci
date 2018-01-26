import os

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
names = os.listdir(scenes_dir)
for name in names:
    filename = os.path.join(scenes_dir, name, name + '.blend')
    if os.path.isfile(filename):
        scenes[name] = filename

# logs
logs_dir = os.path.join(ci_dir, 'logs')

# website
www_dir = os.path.join(ci_dir, 'www')
www_images_dir = os.path.join(www_dir, 'images')
master_json = os.path.join(www_dir, 'master.json')
diffs_json = os.path.join(www_dir, 'diffs.json')
tags_json = os.path.join(www_dir, 'tags.json')
