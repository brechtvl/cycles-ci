#!/usr/bin/python3

import config
import deploy
import os
import shutil
import statistics
import sys
import util

# update blender to specified revision
def update_blender(revision, log_dir):
    update_filepath = os.path.join(log_dir, 'update_' + revision + '.log')
    update_log = open(update_filepath, 'w')

    util.run(['git', 'clean', '-f', '-d'], update_log, config.blender_dir)
    util.run(['git', 'reset', '--hard', 'HEAD'], update_log, config.blender_dir)
    util.run(['git', 'fetch', 'origin', 'master:master'], update_log, config.blender_dir)

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
 
# get median render time for equal time renders
def get_median_render_time(log_dir, scene):
    times, mems = deploy.parse_logs(log_dir, scene)

    if not len(times):
        return None

    return statistics.median(times)

# get sample factor for equal time renders
def compute_sample_factor(revision, device, scene):
    if not revision.endswith('-eqtime'):
        return 1.0

    new_revision = revision[:-len('-eqtime')]
    new_log_dir = os.path.join(config.logs_dir, new_revision, device['id'])
    new_time = get_median_render_time(new_log_dir, scene)

    ref_revision = '-'.join(revision.split('-')[:2]) + '-ref'
    ref_log_dir = os.path.join(config.logs_dir, ref_revision, device['id'])
    ref_time = get_median_render_time(ref_log_dir, scene)

    if not ref_time or not new_time:
        return 0.0

    return ref_time / new_time

# run benchmarks for each scene
def benchmark(revision, log_dir, device):
    for run in range(0, device['runs']):
        for scene, filename in sorted(config.scenes.items()):
            image = os.path.join(log_dir, scene + '_')
            image_ext = image + '0001.png'

            scene_log_filepath = os.path.join(log_dir, scene + '_run' + str(run) + '.log')
            if os.path.exists(scene_log_filepath):
                continue

            sample_factor = device['sample_factor']
            sample_factor *= compute_sample_factor(revision, device, scene)

            cmd = [config.blender_exe, '--debug-cycles', '-b', filename,
                   '-P', os.path.join(config.scripts_dir, 'blender_setup.py'),
                   '-o', image, '-F', 'PNG', '-x', '1', '-f', '1',
                   '--', device['type'], str(device['tile_size']), str(sample_factor)]

            if os.path.exists(image_ext):
                os.remove(image_ext)

            scene_log = open(scene_log_filepath, "w")
            util.run(cmd, scene_log, log_dir)
            scene_log.close()

            if not os.path.exists(image_ext):
                os.remove(scene_log_filepath)

            cache_filepath = os.path.join(log_dir, scene + '.cache')
            if os.path.exists(cache_filepath):
                os.remove(cache_filepath)

        deploy.export_all()

def execute(revisions, force=False):
    # update
    update_log = None
    build_log = None

    # run benchmarks for each device
    for device in config.devices:
        if not device['available']:
            continue

        for revision in revisions:
            # test if we already completed this
            if not force and is_done(revision, device):
                continue

            # create work directory
            log_dir = create_log_dir(revision, device)

            try:
                # update and build only if needed
                update_blender(revision, log_dir)
                build_blender(revision, log_dir)
            except util.RunException as e:
                write_failed(log_dir)
                continue

            write_description(log_dir)

            try:
                benchmark(revision, log_dir, device)
            except util.RunException as e:
                write_failed(log_dir)
                continue

            write_complete(log_dir)
            break

# fetch tags from local remote and create corresponding directories
def update_local_tags():
    # delete tags
    old_tags = util.parse(['git', 'tag'], cwd=config.blender_dir).split('\n')
    for tag in old_tags:
        tag = tag.strip()

        if tag.startswith('ci-'):
            util.run(['git', 'tag', '-d', tag], cwd=config.blender_dir)

    # fetch tags
    try:
        util.run(['git', 'fetch', '--tags', 'local'], cwd=config.blender_dir)
    except util.RunException as e:
        return

    # detect tags
    new_tags = util.parse(['git', 'tag'], cwd=config.blender_dir).split('\n')
    for tag in new_tags:
        tag = tag.strip()

        if tag.startswith('ci-'):
            os.makedirs(os.path.join(config.logs_dir, tag), exist_ok=True)

    # remove logs from deleted tags
    for tag in old_tags:
        if tag not in new_tags:
            tag_dir = os.path.join(config.logs_dir, tag)
            if os.path.isdir(tag_dir):
                shutil.rmtree(tag_dir)
