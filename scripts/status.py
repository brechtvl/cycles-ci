#!/usr/bin/python3

import benchmark
import config
import paths
import os

# test if build is complete or failed
def is_done(revision, device):
    log_dir = os.path.join(paths.logs_dir, revision, device['id'])
    return os.path.isfile(os.path.join(log_dir, 'complete.log')) or \
           os.path.isfile(os.path.join(log_dir, 'failed.log'))

# detect revisions
benchmark.update_local_tags()

ci_ref_revisions = []
ci_revisions = []
revisions = []

for revision in sorted(os.listdir(paths.logs_dir)):
    log_dir = os.path.join(paths.logs_dir, revision)
    if os.path.isdir(log_dir):
        if revision.startswith('ci-'):
            if revision.endswith('-ref') or revision.endswith('-pre'):
                ci_ref_revisions += [revision]
            else:
                ci_revisions += [revision]
        else:
            revisions += [revision]

# benchmark in this order to make equal time comparisons work
all_revisions = ci_ref_revisions + ci_revisions + revisions

# list benchmarks for each device
for device in config.devices:
    if not device['available']:
        continue

    for revision in all_revisions:
        # test if we already completed this
        if is_done(revision, device):
            continue

        print(revision, device['id'])

