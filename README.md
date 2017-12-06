# Requirements:

Please install all requirements before executing:
```
pip install -r requirements.txt
```

**Note:** `pypiwin32` is requirement only for `Windows` platform. <br/>
**Note2:** It is expected that docker is an Linux instance


# Usage:

1. Place `docker_copy.py` and *(optional)* `docker_copy.conf` into git repository from which you willing to copy files into running container
2. Specify container id by one of the following methods:
    * Add in `docker_copy.conf` as `[Optional]docker_container_id` parameter
    * Pass container id as argument: `docker_copy.py <abc123456_id>`
    * Program can pick up automatically id of running container if it is the only one container which currently running
    * Select option from list - if multiples containers are currently running
3. *(Optional)* Specify path mapping in `docker_copy.conf` as `[Optional]path_mapping` if project files path is different from container path where: `key` is local path and `value` is container path <br/>
    ```
    Example:
    path_mapping = {"local_dir": "docker_path"}
    ``` 
    
    
# Config:
`docker_copy.conf` has several options:

1. `docker_container_id` - takes container id or empty

```
docker_container_id = 8bcc66aa8ad7
```

2. `path_mapping` - takes dictionary of pairs: `{local_path: docker_path}`

```
path_mapping = {"*": "/opt/myapp"} - would map all changed files to /opt/myapp/*
or
{"/tmp/path": "/opt/myapp"} - would map all changed files in /tmp/path to /opt/myapp/*

mapping can be combained:
{"*": "/opt/myapp", "/tmp/path": "/opt/myapp", "keyN": "valN"}

```

3. `other_files` - takes dictionary of pairs: `{"full_local_path": "docker_path"}` - 
and copy other additional files (outside of git projects) to the container.<br/> 
Logic is the same as with `path_mapping`