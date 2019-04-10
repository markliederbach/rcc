import os
import tarfile


class FileManager:
    def __init__(self, tar_filepath, dest_dir):
        self.tar_filepath = tar_filepath
        self.dest_dir = dest_dir

    def untar(self):
        with tarfile.open(self.tar_filepath) as tar:
            tar.extractall(path=self.dest_dir)

    def tar(self, filepath, source_dir):
        with tarfile.open(filepath, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
