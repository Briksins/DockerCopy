import ConfigParser
import sys
import os

import docker
from git import Repo


optional_config_file = "docker_copy.conf"


class DockerCopy:

    def __init__(self):
        self.conf = ConfigParser.ConfigParser(allow_no_value=True)
        self.project_path = None
        self.repo = None
        self.docker_client = None
        self.docker_selected_container = None
        self.changed_files = []
        self.changed_files_full_path = []

        self.init_conf()
        self.init_args()
        self.init_docker()

        self.get_changes_from_git()

    def init_conf(self):
        if optional_config_file is None:
            return
        try:
            self.conf.read(optional_config_file)
        except Exception, e:
            print "Failed to read config file. Exception: " + str(e.message)

    def init_args(self):
        args = sys.argv
        self.project_path = os.path.dirname(os.path.realpath(args[0]))
        if len(args) > 1:
            self.conf.set("Optional", "docker_container_id", args[1])

    def init_docker(self):
        self.docker_selected_container = self.conf.get("Optional", "docker_container_id")
        self.docker_client = docker.from_env()
        running_containers = self.docker_client.containers.list()
        if len(running_containers) < 1:
            print "There are no running containers to copy files to..."
            sys.exit(1)

        if self.docker_selected_container is not None:
            for running_container in running_containers:
                if str(running_container.short_id).startswith(self.docker_selected_container):
                    return

            print "Specified Docker container id " + self.docker_selected_container + "is not currently running!"
            print "Please update config parameter or pass it as argument or select from running containers list"
            sys.exit(1)
        else:
            if len(running_containers) == 1:
                self.docker_selected_container = running_containers[0].short_id
            else:
                self.ask_for_exact_docker_container(running_containers)

    def ask_for_exact_docker_container(self, running_containers):
        print "Please specify exact Docker container to copy files to: \n"
        print "Index - ID"
        index = 1
        for running_container in running_containers:
            print "[" + str(index) + "] - " + running_container.short_id
            index += 1

        while True:
            user_input = raw_input("Make your choice: ")
            if user_input.isdigit():
                selected_option = int(user_input) - 1
                if 0 <= selected_option <= len(running_containers):
                    self.docker_selected_container = running_containers[selected_option].short_id
                    return
            print "Wrong input, please try again\n"

    def get_changes_from_git(self):
        try:
            self.repo = Repo(self.project_path)
        except Exception, e:
            print "Failed to get Git Repository. Exception: " + type(e).__name__ + " - " + str(e.message)
            sys.exit(-1)
        # Get Changes from commit files
        self.get_git_dif()
        # Get changes from upstaged files
        self.get_git_dif('HEAD')

        print self.changed_files_full_path

    def get_git_dif(self, diff_rule=None):
        for changed_file in self.repo.index.diff(diff_rule):
            if "/" in changed_file.a_path:
                self.changed_files_full_path.append(os.path.join(self.project_path, *changed_file.a_path.split("/")))
                self.changed_files.append(os.path.join(*changed_file.a_path.split("/")))
            else:
                self.changed_files_full_path.append(os.path.join(self.project_path, changed_file.a_path))
                self.changed_files.append(changed_file)


DockerCopy()
