# Cycles CI

Benchmarking and testing for the Cycles renderer.
https://brechtvl.github.io/cycles-ci/

### Setup

```
# Add scenes
git clone git@github.com:brechtvl/cycles-ci-scenes.git scenes

# Setup Blender build
git clone git://git.blender.org/blender.git blender
mkdir build && cd build
cmake ../blender
...

# Edit configuration and run server
vim scripts/config.py
ssh-agent ./scripts/server.py

# Create empty directories matching Git hashes or Differential revisions
# to add to the list of revisions to benchmark.
mkdir logs/abc1234
mkdir logs/D1234
```

Browse http://localhost:4000 to see results.

### Local Tags

The server can pull specially named tags from a git repository, and automatically
benchmark them. This repository could be on the same computer, or a separate one
to avoid timing noise.

All tags named ci-mytest-\* will be grouped as ci-mytest, with ci-mytest-ref
indicating the revision for the reference render time.

```
# On the server
cd cycles-ci/blender
git remote add local ssh://workpc:/home/user/blender/.git

# On the work computer
cd /home/user/blender
git tag ci-mytest-ref
... commit changes ...
git tag ci-mytest-variation1
... commit changes ...
git tag ci-mytest-variation2
```
