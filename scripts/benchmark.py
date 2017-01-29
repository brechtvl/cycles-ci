#!/usr/bin/python3

import config
import deploy
import os
import shutil
import sys
import util

# update blender to specified revision
def update_blender(revision):
    update_filepath = os.path.join(config.logs_dir, 'update_' + revision + '.log')
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
    return update_filepath

# build blender
def build_blender(revision):
    build_filepath = os.path.join(config.logs_dir, 'build_' + revision + '.log')
    build_log = open(build_filepath, "w")
    util.run(['cmake', config.blender_dir], build_log, config.build_dir)
    util.run(['make', '-j8', 'install'], build_log, config.build_dir)
    build_log.close()

    return build_filepath

# write description.log
def write_description(work_dir):
    description_log = open(os.path.join(work_dir, 'description.log'), "w")
    subject =  util.parse(['git', 'log', '-n1', '--format=%s'], config.blender_dir)
    description_log.write(subject)
    description_log.close()

# write complete.log
def write_complete(log_dir):
    complete_log = open(os.path.join(log_dir, 'complete.log'), "w")
    complete_log.write('complete')
    complete_log.close()

# test if build is complete
def is_complete(revision, device):
    log_dir = os.path.join(config.logs_dir, revision, device['id'])
    return os.path.isfile(os.path.join(log_dir, 'complete.log'))

# clear log files from previous run
def clear_logs(log_dir):
    for f in os.listdir(log_dir):
        filepath = os.path.join(log_dir, f)
        if f.endswith('.log') or f.endswith('.png'):
            if os.path.isfile(filepath):
                os.remove(filepath)

# create log directory and temporary working directory
def create_work_dir(revision, device, update_filepath):
    log_dir = os.path.join(config.logs_dir, revision, device['id'])
    os.makedirs(log_dir, exist_ok=True)

    if config.use_tmp_dir:
        work_dir = os.path.join(log_dir, 'work')
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        os.makedirs(work_dir)
    else:
        clear_logs(log_dir)
        work_dir = log_dir

    return log_dir, work_dir
 
# move files from temporary working to final log directory
def cleanup_work_dir(work_dir, log_dir):
    if config.use_tmp_dir:
        clear_logs(log_dir)
        for f in os.listdir(work_dir):
            shutil.move(os.path.join(work_dir, f), os.path.join(log_dir, f))
        shutil.rmtree(work_dir)

# run benchmarks for each scene
def benchmark(work_dir, device):
    for run in range(0, config.runs):
        for scene, filename in sorted(config.scenes.items()):
            image = os.path.join(work_dir, scene + '_')
            image_ext = image + '0001.png'
            cmd = [config.blender_exe, '--debug-cycles', '-b', filename,
                   '-P', os.path.join(config.scripts_dir, 'blender_setup.py'),
                   '-o', image, '-F', 'PNG', '-x', '1', '-f', '1',
                   '--', device['type'], str(device['tile_size']), str(device['sample_factor'])]

            if os.path.exists(image_ext):
                os.remove(image_ext)

            scene_log_filepath = os.path.join(work_dir, scene + '_run' + str(run) + '.log')
            scene_log = open(scene_log_filepath, "w")
            util.run(cmd, scene_log, work_dir)
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
        if not force and is_complete(revision, device):
            continue

        try:
            # update and build only if needed
            if not built:
                update_log = update_blender(revision)
                build_log = build_blender(revision)
                built = True

            # create work directory
            log_dir, work_dir = create_work_dir(revision, device, update_log)

            # copy update and build logs into each work directory
            write_description(work_dir)
            shutil.copy(update_log, os.path.join(work_dir, 'update.log'))
            shutil.copy(build_log, os.path.join(work_dir, 'build.log'))

            benchmark(work_dir, device)
            cleanup_work_dir(log_dir, work_dir)
        except util.RunException as e:
            pass

        write_complete(log_dir)

    # remove temporary update and build logs
    if update_log:
        os.remove(update_log)
    if build_log:
        os.remove(build_log)

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

