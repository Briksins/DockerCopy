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

        # Get Changes from commit files
        self.get_git_dif()

        # Get changes from upstaged files
        self.get_git_dif('HEAD')

        print self.changed_files

    def get_git_dif(self, diff_rule=None):
        for changed_files in self.repo.index.diff(diff_rule):
            if "/" in changed_files.a_path:
                self.changed_files.append(os.path.join(self.project_path, *changed_files.a_path.split("/")))
            else:
                self.changed_files.append(os.path.join(self.project_path, changed_files.a_path))


DockerCopy()
