import ConfigParser
import json
import sys
import os
import subprocess
import docker
from git import Repo


optional_config_file = "docker_copy.conf"


class DockerCopy:

    def __init__(self):
        self.conf = ConfigParser.ConfigParser(allow_no_value=True)
        self.project_path = None
        self.project_name = None
        self.repo = None
        self.docker_client = None
        self.docker_selected_container = None
        self.other_files = None
        self.changed_files = []
        self.copy_to_all = False
        self.folder_created = {}
        self.mapped_paths = None
        self.other_files = None

        self.init_conf()
        self.init_args()
        self.init_docker()

        self.get_changes_from_git()
        self.handle_other_files()
        self.copy_modified_git_files_to_docker()

    def init_conf(self):
        if optional_config_file is None:
            return
        try:
            self.conf.read(optional_config_file)

            mapping_paths = self.conf.get("Optional", "path_mapping")
            if mapping_paths is not None and len(mapping_paths) > 0:
                try:
                    self.mapped_paths = json.loads(mapping_paths)
                except Exception, e:
                    print "Failed to parse mapped paths from config. Exception: " + str(e.message)
                    sys.exit(-1)

            other_files = self.conf.get("Optional", "other_files")
            if other_files is not None and len(other_files) > 0:
                try:
                    self.other_files = json.loads(other_files)
                except Exception, e:
                    print "Failed to parse other files from config. Exception: " + str(e.message)
                    sys.exit(-1)
        except Exception, e:
            print "Failed to read config file. Exception: " + str(e.message)

    def init_args(self):
        args = sys.argv
        self.project_path = os.path.dirname(os.path.realpath(args[0]))
        head, self.project_name = os.path.split(self.project_path)

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
        print "[0] \t-\tCopy to all running containers"

        index = 1
        for running_container in running_containers:
            print "[" + str(index) + "] \t-\t" + running_container.short_id + "\t-\t" + running_container.image.tags[0]
            index += 1
        while True:
            user_input = raw_input("Make your choice: ")
            if user_input.isdigit():
                selected_option = int(user_input)
                if selected_option == 0:
                    self.copy_to_all = True
                    return
                if 0 < selected_option <= len(running_containers):
                    self.docker_selected_container = running_containers[selected_option-1].short_id
                    return
            print "Wrong input, please try again\n"

    def get_changes_from_git(self):
        try:
            self.repo = Repo(self.project_path)
        except Exception, e:
            print "Failed to get Git Repository. Exception: " + type(e).__name__ + " - " + str(e.message)
            sys.exit(-1)
        # Get Changes from tracked files
        self.get_git_dif()
        # Get changes from unstaged files
        self.get_git_dif('HEAD')

    def get_git_dif(self, diff_rule=None):
        for changed_file in self.repo.index.diff(diff_rule):
            if "/" not in changed_file.a_path:
                self.changed_files.append({
                    "local": os.path.join(self.project_path, changed_file.a_path),
                    "docker": self.handle_docker_path_mapping("*")
                })
            else:
                self.changed_files.append({
                    "local": os.path.join(self.project_path, *changed_file.a_path.split("/")),
                    "docker": self.handle_docker_path_mapping(changed_file.a_path, True)
                })

    def handle_other_files(self):
        other_files = self.conf.get("Optional", "other_files")
        if other_files is None or len(other_files) == 0:
            return

        for other_file in other_files:
            self.changed_files.append({
                "local": other_file,
                "docker": other_files[other_file]
            })

    def handle_docker_path_mapping(self, changed_file, split=False):
        if self.mapped_paths is None:
            if not split:
                return "/opt/" + self.project_name + changed_file.replace("*", "/")
            else:
                return "/opt/" + self.project_name + "/" + os.path.split(changed_file)[0] + "/"
        else:
            if not split:
                    if changed_file in self.mapped_paths:
                        return self.mapped_paths[changed_file] + "/"
            else:
                changed_path = os.path.split(changed_file)[0]
                for mapped_path_key in self.mapped_paths:
                    if changed_path in mapped_path_key:
                        return self.mapped_paths[mapped_path_key] + "/"

                if "*" in self.mapped_paths:
                    return self.mapped_paths["*"] + "/" + changed_path + "/"

            return "/opt/" + self.project_name + "/" + changed_file + "/"

    def copy_modified_git_files_to_docker(self):
        for change_set in self.changed_files:
            self.copy_to_docker(change_set["local"], change_set["docker"])

    def copy_to_docker(self, local_path, docker_path):
        if not self.copy_to_all:
            self.handle_new_folders_in_docker(self.docker_selected_container, docker_path)
            self.execute_command("docker cp " + local_path + " " + self.docker_selected_container + ":" + docker_path)
        else:
            for container in self.docker_client.containers.list():
                self.handle_new_folders_in_docker(container.short_id, docker_path)
                self.execute_command("docker cp " + local_path + " " + container.short_id + ":" + docker_path)

    def handle_new_folders_in_docker(self, container_id, docker_path):
        if docker_path == "/":
            return

        if container_id in self.folder_created:
            for path in self.folder_created[container_id]:
                if path == docker_path:
                    return

        self.execute_command("docker exec -d " + container_id + " mkdir -p " + docker_path)

        if container_id in self.folder_created:
            self.folder_created[container_id].append(docker_path)
        else:
            self.folder_created[container_id] = [docker_path]

    def execute_command(self, cmd, async=False):
        print cmd
        if async:
            subprocess.Popen(cmd)
        else:
            sp = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = sp.communicate()
            if out is not None and len(out) > 0:
                print "Output: \n" + out
            if err is not None and len(err) > 0:
                print "Error: \n" + err


DockerCopy()
