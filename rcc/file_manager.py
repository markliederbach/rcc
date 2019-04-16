import os
import shutil
import tarfile


class FileManager:
    def __init__(self, tar_filepath, dest_dir):
        self.tar_filepath = tar_filepath
        self.dest_dir = dest_dir
        self.remove(self.dest_dir)

    def untar(self):
        with tarfile.open(self.tar_filepath) as tar:
            tar.extractall(path=self.dest_dir)

    def tar(self, filepath, rel_path):
        path = os.path.join(self.dest_dir, rel_path)
        with tarfile.open(filepath, "w:gz") as tar:
            tar.add(path, arcname=os.path.basename(path))
        self.remove(self.dest_dir)

    def remove(self, path):
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
