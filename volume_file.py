import os

import fasteners

dir_path = os.path.dirname(os.path.realpath(__file__))
VOLUME_FILE = f'{dir_path}/volume.conf'
VOLUME_FILE_LOCK = f'{dir_path}/volume.lock'

lock = fasteners.InterProcessLock(VOLUME_FILE_LOCK)


def get_current_volume():
    lock.acquire(blocking=True)
    with open(VOLUME_FILE, 'r') as f:
        volume = f.read()
    lock.release()
    return float(volume)


def set_current_volume(volume):
    lock.acquire(blocking=True)
    with open(VOLUME_FILE, 'w') as f:
        f.write(str(volume))
    lock.release()
