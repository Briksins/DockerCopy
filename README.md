# Requirements:

Please install all requirements before executing:
```
pip install -r requirements.txt
```

**Note:** `pypiwin32` is requirement only for `Windows` platform.


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
    
    
**Development Still in Progress .......**
