
import config
import glob
import os
import util

# rename to myimage_xxxsh1hashxxx.png
def image_hashify(filepath):
    result = util.parse(['oiiotool', '--hash', filepath])
    filehash = result.split('\n')[1].strip().split(' ')[1]
    newpath = '_'.join(filepath.split('_')[:-1]) + '_' + filehash + '.png'
    os.rename(filepath, newpath)

    return newpath

# extra hash from myimage_xxxsha1hashxxx.png
def image_hash(filepath):
    return os.path.splitext(os.path.basename(filepath))[0].split('_')[-1]

# extract scene name
def image_scene(filepath):
    return '_'.join(os.path.basename(filepath).split('_')[:-1])

# test if images are approximately equal
def image_matches(filepath1, filepath2):
    if image_scene(filepath1) != image_scene(filepath2):
        return False
    if image_hash(filepath1) == image_hash(filepath2):
        return True

    try:
        util.run(['oiiotool', '--diff', '--fail', '0.001', '--failpercent', '1', filepath1, filepath2])
    except util.RunException as e:
        return False

    return True

# put hash in filename and deduplicate
def get_filepath(log_dir, scene):
    os.makedirs(config.www_images_dir, exist_ok=True)
    filepath = os.path.join(log_dir, scene + '_0001.png')

    if os.path.exists(filepath):
        # rename image to include hash
        filepath = image_hashify(filepath)

        # find duplicates
        scene = image_scene(filepath)
        if 'ci-' in log_dir:
            others = list(glob.iglob(os.path.join(config.logs_dir, 'ci-*', '*', scene + '_*.png')))
        else:
            others = list(glob.iglob(os.path.join(config.logs_dir, '*', '*', scene + '_*.png')))

        for otherpath in others:
            if image_matches(filepath, otherpath):
                if otherpath.endswith('_0001.png'):
                    newpath = os.path.join(os.path.dirname(otherpath), os.path.basename(filepath))
                    os.rename(otherpath, newpath)
                    return filepath
                else:
                    newpath = os.path.join(os.path.dirname(filepath), os.path.basename(otherpath))
                    os.rename(filepath, newpath)
                    return newpath

        return filepath
    else:
        # find filepath with hash
        filepaths = list(glob.iglob(os.path.join(log_dir, scene + '_*.png')))
        return filepaths[0] if len(filepaths) else None

# copy and compress image
def copy_compressed(filepath, destdir):
    name, ext = os.path.splitext(os.path.basename(filepath))
    destname = name + '.jpg'
    destpath = os.path.join(destdir, destname)

    if not os.path.exists(destpath):
        if image_scene(filepath) == 'classroom':
            util.run(['oiiotool', filepath, '--quality', '90', '--resize', '50%', '-o', destpath])
        else:
            util.run(['oiiotool', filepath, '--quality', '90', '-o', destpath])

    return destname
