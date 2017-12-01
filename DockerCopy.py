from git import Repo
import os


docker_running_image_id = "abef04dghr"

path_mapping = {
    "": "",
}


class DockerCopy:

    def __init__(self):
        self.changed_files = []
        self.project_path = os.path.dirname(os.path.realpath(__file__))
        self.repo = Repo(self.project_path)
        self.get_changes_from_git()

    def get_changes_from_git(self):
        for changed_file in self.repo.untracked_files:
            print os.path.join(self.project_path, changed_file)


DockerCopy()
