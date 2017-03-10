#!/usr/bin/python3

import config
import deploy
import os
import shutil
import sys
import util

# update blender to specified revision
def update_blender(revision, log_dir):
    update_filepath = os.path.join(log_dir, 'update_' + revision + '.log')
    update_log = open(update_filepath, 'w')

    util.run(['git', 'clean', '-f', '-d'], update_log, config.blender_dir)
    util.run(['git', 'reset', '--hard', 'HEAD'], update_log, config.blender_dir)
    util.run(['git', 'checkout', 'master'], update_log, config.blender_dir)
    util.run(['git', 'pull', 'origin', 'master'], update_log, config.blender_dir)

    if revision.startswith('D'):
        before = revision.endswith("~1")
        if before:
            revision = revision[:-2]

        branch_name = 'arcpatch-' + revision
        util.run(['git', 'branch', '-D', branch_name], update_log, config.blender_dir, silent=True)
        util.run(['arc', 'patch', '--force', revision], update_log, config.blender_dir)
        revision = branch_name

        if before:
            revision += "~1"

    util.run(['git', 'checkout', revision], update_log, config.blender_dir)

    update_log.close()

# build blender
def build_blender(revision, log_dir):
    build_filepath = os.path.join(log_dir, 'build_' + revision + '.log')
    build_log = open(build_filepath, "w")
    util.run(['cmake', config.blender_dir], build_log, config.build_dir)
    util.run(['make', '-j8', 'install'], build_log, config.build_dir)
    build_log.close()

# write description.log
def write_description(log_dir):
    description_log = open(os.path.join(log_dir, 'description.log'), "w")
    subject =  util.parse(['git', 'log', '-n1', '--format=%s'], config.blender_dir)
    description_log.write(subject)
    description_log.close()

# write complete.log
def write_complete(log_dir):
    complete_log = open(os.path.join(log_dir, 'complete.log'), "w")
    complete_log.write('complete')
    complete_log.close()

# write failed.log
def write_failed(log_dir):
    failed_log = open(os.path.join(log_dir, 'failed.log'), "w")
    failed_log.write('failed')
    failed_log.close()

# test if build is complete or failed
def is_done(revision, device):
    log_dir = os.path.join(config.logs_dir, revision, device['id'])
    return os.path.isfile(os.path.join(log_dir, 'complete.log')) or \
           os.path.isfile(os.path.join(log_dir, 'failed.log'))

# create log directory
def create_log_dir(revision, device):
    log_dir = os.path.join(config.logs_dir, revision, device['id'])
    os.makedirs(log_dir, exist_ok=True)

    return log_dir
 
# run benchmarks for each scene
def benchmark(log_dir, device):
    for run in range(0, config.runs):
        for scene, filename in sorted(config.scenes.items()):
            image = os.path.join(log_dir, scene + '_')
            image_ext = image + '0001.png'

            scene_log_filepath = os.path.join(log_dir, scene + '_run' + str(run) + '.log')
            if os.path.exists(image_ext) and os.path.exists(scene_log_filepath):
                continue

            cmd = [config.blender_exe, '--debug-cycles', '-b', filename,
                   '-P', os.path.join(config.scripts_dir, 'blender_setup.py'),
                   '-o', image, '-F', 'PNG', '-x', '1', '-f', '1',
                   '--', device['type'], str(device['tile_size']), str(device['sample_factor'])]

            if os.path.exists(image_ext):
                os.remove(image_ext)

            scene_log = open(scene_log_filepath, "w")
            util.run(cmd, scene_log, log_dir)
            scene_log.close()

            if not os.path.exists(image_ext):
                os.remove(scene_log_filepath)

        deploy.export_all()

def execute(revision, force=False):
    # update
    update_log = None
    build_log = None
    built = False

    # run benchmarks for each device
    for device in config.devices:
        # test if we already completed this
        if not force and is_done(revision, device):
            continue

        # create work directory
        log_dir = create_log_dir(revision, device)

        try:
            # update and build only if needed
            if not built:
                update_blender(revision, log_dir)
                build_blender(revision, log_dir)
                built = True
        except util.RunException as e:
            write_failed(log_dir)
            continue

        write_description(log_dir)

        try:
            benchmark(log_dir, device)
        except util.RunException as e:
            write_failed(log_dir)
            continue

        write_complete(log_dir)

# fetch tags from local remote and create corresponding directories
def update_local_tags():
    try:
        util.run(['git', 'fetch', '--tags', 'local'], cwd=config.blender_dir)
    except util.RunException as e:
        return

    tags = util.parse(['git', 'tag'], cwd=config.blender_dir).split('\n')
    for tag in tags:
        tag = tag.strip()

        if tag.startswith('ci-'):
            os.makedirs(os.path.join(config.logs_dir, tag), exist_ok=True)

