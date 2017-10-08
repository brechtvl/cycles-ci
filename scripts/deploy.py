#!/usr/bin/python3

import config
import datetime
import image
import json
import os
import pickle
import shutil
import statistics
import util

# parse time and memory from logs
def parse_logs(log_dir, scene):
    # use cached data for speed
    cache_filepath = os.path.join(log_dir, scene + '.cache')
    if os.path.isfile(cache_filepath):
        return pickle.load(open(cache_filepath, "rb"))

    times = []
    mems = []

    for run in range(1, 32):
        log_filepath = os.path.join(log_dir, scene + '_run' + str(run) + '.log')

        if not os.path.isfile(log_filepath):
            continue

        log_file = open(log_filepath, 'r')

        for line in log_file.readlines():
            label = "Render time (without synchronization): "
            if line.find(label) != -1:
                token = line[line.find(label) + len(label):]
                times += [float(token.strip())]
             
            label = "Peak: "
            if line.find(label) != -1:
                token = line.strip().split(' ')[1]
                token = token.replace(',', '')
                mems += [float(token) / (1024.0 * 1024.0)]

    data = times, mems
    pickle.dump(data, open(cache_filepath, "wb"))

    return data

# get name from revision number
def revision_date(revision):
    if revision.startswith('D'):
        return int(util.parse(['git', 'log', '-n1', 'arcpatch-' + revision, '--format=%at'], config.blender_dir))
    else:
        return int(util.parse(['git', 'log', '-n1', revision, '--format=%at'], config.blender_dir))

# is a differential revision
def revision_is_diff(revision):
    return revision[0] == 'D'

# commit dates are not chronological due to merge/rebase, so we sort
# the revisions following the order in the master branch
def sort_master_revisions(revision_map):
    result = util.parse(['git', 'log', '15fd758..master', '--format=%h %at'], config.blender_dir)

    sorted_revisions = []
    for line in reversed(result.split('\n')):
        revision, date = line.split(' ')
        if revision in revision_map:
            sorted_revisions += [[revision_map[revision], int(date)]]

    # fudge dates to have a proper order, git commit dates are not ordered
    for j in range(0, 10):
        modified = False

        for i in range(1, len(sorted_revisions) - 1):
            sorted_revisions[i][1] = (sorted_revisions[i-1][1] + sorted_revisions[i+1][1]) // 2

    return sorted_revisions

# get list of revisions between two commits
def revisions_list(last, current):
    if last == current or last == '':
        revision_range = current + '~1..' + current
    else:
        revision_range = last + '..' + current

    result = util.parse(['git', 'log', revision_range, '--format=%h %at %s', '--', 'intern/cycles'], config.blender_dir)
    lines = []
    for line in result.split('\n'):
        if len(line):
            revision, _, rest = line.partition(' ')
            date, _, subject = rest.partition(' ')
            lines += [{'hash': revision, 'date': int(date), 'subject': subject}]

    return lines;

def export_master():
    data_devices = []

    # one graph for each device
    for device in config.devices:
        # JSON data layout is like a spreadsheat table, with colums, rows and cells
        # create one column for revision labels, and one column for each scene
        cols = []
        cols += [{'id': '', 'label': 'revision', 'type': 'date'}]
        for scene in sorted(config.scenes.keys()):
            cols += [{'id': '', 'label': scene, 'type': 'number'}]
            cols += [{'id': '', 'label': None, 'role': 'tooltip', 'type': 'string', 'p': {'html': True}}]
            cols += [{'id': '', 'label': None, 'role': 'interval', 'type': 'number'}]
            cols += [{'id': '', 'label': None, 'role': 'interval', 'type': 'number'}]

        # find master logs
        revision_map = {}

        for revision in sorted(os.listdir(config.logs_dir)):
            log_dir = os.path.join(config.logs_dir, revision, device['id'])
            if not os.path.isdir(log_dir):
                continue

            # directory name to revision
            if revision_is_diff(revision):
                continue

            revision_map[revision] = revision

        # create one row for each master log
        rows = []
        commits = []
        images = []
        last_revision = ''

        for revision, fake_date in sort_master_revisions(revision_map):
            log_dir = os.path.join(config.logs_dir, revision, device['id'])
            date = revision_date(revision)

            # get all revisions between last and current data point
            revisions = revisions_list(last_revision, revision)

            # create tooltip
            subject = util.parse(['git', 'log', '-n1', '--format=%s', revision], config.blender_dir)
            tooltip_start = '<div class="tooltip">Time: <b>%.2fs</b><br/>Peak: %.2fMB<br/>'
            tooltip_end = 'Date: ' + datetime.datetime.fromtimestamp(date).strftime('%Y-%m-%d') + '<br/>'
            tooltip_end += 'Revision: <b>' + revision + '</b> ' + subject[:60] + '<br/>'
            if len(revisions) > 1:
                tooltip_end += '<i>(%d commits, click point for details)</i><br/>' % len(revisions)

            # find lowest render time for each scene
            log_times = []
            log_mems = []
            log_variance = []
            row_images = []
            for scene in sorted(config.scenes.keys()):
                scene_times, scene_mems = parse_logs(log_dir, scene)

                if len(scene_times):
                    log_times += [statistics.median(scene_times)]
                    log_mems += [statistics.median(scene_mems) if len(scene_mems) > 1 else 0]
                    log_variance += [statistics.stdev(scene_times) if len(scene_times) > 1 else 0.0]

                    imagepath = image.get_filepath(log_dir, scene)
                    imagename = image.copy_compressed(imagepath, config.www_images_dir)
                    row_images += [imagename]

            if sum(log_times) != 0.0:
                # create row
                row = [{'f': None, 'v': 'Date({0})'.format(fake_date * 1000)}]
                for time, mem, variance in zip(log_times, log_mems, log_variance):
                    row += [{'f': None, 'v': time}]
                    row += [{'f': None, 'v': (tooltip_start % (time, mem)) + tooltip_end}]
                    row += [{'f': None, 'v': time - variance}]
                    row += [{'f': None, 'v': time + variance}]

                rows += [{'c': row}]
                commits += [revisions]
                images += [row_images]
                last_revision = revision
            else:
                pass

        data = {'cols': cols, 'rows': rows}
        label = device['name'] + ', ' + device['os']
        data_devices += [{'id': device['id'], 'name': label, 'data': data, 'commits': commits, 'images': images}]

    data_filepath = os.path.join(config.master_json)
    data_file = open(data_filepath, 'w')
    data_file.write(json.dumps(data_devices)) #, indent=2))
    data_file.close()

def export_comparisons(revision_groups, json_filename):
    data_diffs = []

    for name, revisions in reversed(sorted(revision_groups.items())):
        data_devices = []
        description = ''
        tooltip = '<div class="tooltip">%s<br/>Time: <b>%.2fs</b><br/>Peak: %.2fM<br/>Diff: %.1f%%</div>'

        # one graph for each device
        for device in config.devices:
            num_runs = device['runs'] - 1

            # create revision directories list
            revision_dirs = []
            ready_revisions = []

            for revision in revisions:
                revision_dir = os.path.join(config.logs_dir, revision, device['id'])
                if os.path.isdir(revision_dir):
                    revision_dirs += [revision_dir]
                    ready_revisions += [revision]

            if len(ready_revisions) == 0:
                continue

            # create labels and description
            if revision_is_diff(ready_revisions[0]) and len(ready_revisions) == 2:
                revision_labels = ['Before', 'After']

                description_filepath = os.path.join(revision_dirs[1], 'description.log')
                if os.path.exists(description_filepath):
                    date = revision_date(ready_revisions[1])
                    contents = open(description_filepath, 'r').read()
                    description = contents.strip()
                    description += ' (' + datetime.datetime.fromtimestamp(date).strftime('%b %d %Y') + ')'
            else:
                revision_labels = []
                for revision in ready_revisions:
                    revision_labels += [revision[len(name)+1:]]
                description = ''

            # JSON data layout is like a spreadsheat table, with colums, rows and cells
            # create one column for revision labels, and one column for each scene
            cols = []
            cols += [{'id': '', 'label': 'scene', 'type': 'string'}]

            for revision_label in revision_labels:
                cols += [{'id': '', 'label': revision_label, 'type': 'number'}]
                cols += [{'id': '', 'label': None, 'role': 'tooltip', 'type': 'string', 'p': {'html': True}}]
                for run in range(0, num_runs):
                    cols += [{'id': '', 'label': None, 'role': 'interval', 'type': 'number'}]

            # find before and after render time for each scene
            rows = []
            images = []

            for scene in sorted(config.scenes.keys()):
                revision_times = []
                revision_mems = []
                num_times = 0
                for revision_dir in revision_dirs:
                    times, mems = parse_logs(revision_dir, scene)
                    num_times = max(num_times, len(times))
                    revision_times += [times]
                    revision_mems += [mems]

                if num_times:
                    revision_images = []
                    for revision_dir in revision_dirs:
                        imagepath = image.get_filepath(revision_dir, scene)
                        if imagepath:
                            revision_images += [image.copy_compressed(imagepath, config.www_images_dir)]

                    ref_median = statistics.median(revision_times[0]) if len(revision_times[0]) else 1.0

                    row = [{'f': None, 'v': scene}]
                    row_images = []
                    for label, times, mems, imagename in zip(revision_labels, revision_times, revision_mems, revision_images):
                        median = statistics.median(times) if len(times) else ref_median
                        mem = statistics.median(mems) if len(mems) else 0

                        t = median / ref_median - 1.0
                        row += [{'f': None, 'v': t}]
                        row += [{'f': None, 'v': tooltip % (label, median, mem, t * 100)}]

                        for run in range(0, num_runs):
                            if run < len(times):
                                t = times[run] / ref_median - 1.0
                                row += [{'f': None, 'v': t}]
                            else:
                                row += [{'f': None, 'v': None}]

                        row_images += [imagename] * (2 + num_runs)

                    rows += [{'c': row}]
                    images += [row_images]

            if len(rows):
                data = {'cols': cols, 'rows': rows}
                label = device['name'] + ', ' + device['os']
                data_devices += [{'id': device['id'], 'name': label, 'data': data, 'images': images}]

        if len(data_devices):
            data_diffs += [{'name': name, 'description': description, 'data': data_devices}]

    data_filepath = os.path.join(json_filename)
    data_file = open(data_filepath, 'w')
    data_file.write(json.dumps(data_diffs)) #, indent=2))
    data_file.close()
 
def export_all():
    diffs = {}
    tags = {}

    revisions = sorted(os.listdir(config.logs_dir))

    for revision in revisions:
        log_dir = os.path.join(config.logs_dir, revision)
        if os.path.isdir(log_dir):
            if revision_is_diff(revision):
                # add D??? and the commit before it
                name = revision.split('~')[0]
                diffs[name] = [name + '~1', name]
            elif revision.startswith('ci-'):
                # add all revisions starting with ci-something
                name = '-'.join(revision.split('-')[:2])
                revs = [rev for rev in revisions if rev.startswith(name)]

                # ensure ci-something-ref is the first
                refname = name + '-ref'
                if refname in revs:
                    revs.remove(refname)
                    revs = [refname] + revs

                tags[name] = revs

    export_master()
    export_comparisons(diffs, config.diffs_json)
    export_comparisons(tags, config.tags_json)

if __name__ == "__main__":
    export_all()

