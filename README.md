# SSH-Lite
An easy encapsulation for paramiko library which contains only common operations.
Version 1.1 is migrated from the original code for automatic testing / operation.

## Features

* Interactive shell commands without blocking
    * *send* for sending a command only
	* *send_and_read* is the most common, for sending a command and read all returnes in a timeout period (timeout will be updated after receiving any bytes)
	* *get_buff* for reading all buffers from the terminal in a timeout period
* Uploading or downloading files between local and remote server
* Expect function (may raise an exception for timeout)
* Grep function and keys abbreviations

## QuickStart

install

```shell
pip install ssh-lite
```

or update

```shell
pip install -U ssh-lite
```

a simple example

```python
from ssh_lite import Server

ci = Server("127.0.0.1", "123456", "root")
ci.send_and_read("")    # waiting connection output done, avoid getting extra output before "ls -l" like "Last login: Tue ..."
print(ci.send_and_read("ls -l"))
del ci
```

the effect is like

```
ls -l
total 1736
-rw-r--r-- 1 root  root  1775417 Aug 25  2019 get-pip.py
-rwxrwxrwx 1 root  root      289 Feb 20 12:00 temp.py
-rwxrwxrwx 1 root  root      136 Nov 22 21:18 upload
```

another little complex example to explain the functions

```python
from ssh_lite import Server, KeyAbbr

remote = "/docker_binding_path"
file = "test.file"

with Server("127.0.0.1", "123456", "root", port=22, key_path=None) as ci:  # type: Server  # rsa keys are supported
    ci.debug = True     # to see server inputs and outputs
    ci.get_file("/a_log_file_to_get", ".")      # getting files doesn't need destination filename 
    ci.send_and_read("mkdir -p " + remote, timeout=1)
    ci.send_and_read("rm -f {}*".format(remote), timeout=1)
    ci.put_file("prepare/" + file, remote + file)      # putting files strictly need destination filename
    ci.send_and_read("", timeout=1)
    cmd = 'docker exec -i container_name curl -v "http://127.0.0.1:9990/upload?file=/reference_path/{}&uri=me"'.format(
        file)
    print("inner cmd is: {}".format(cmd))
    ci.send(cmd)
    ci.expect("< HTTP/1.1 200 OK", timeout=30)      # will raise an exception if we cannot see 200 OK response in 30 secs
    ci.send(KeyAbbr.CTRL_C, end="")      # sending a CTRL+C to exit the HTTP2 long connection
    ci.send('exit')       # exit from container to release the connection
```

## Bug report

* Issues and bugs report to rainydew@qq.com.
* Homepage icon leads to my Github project page, issues / PRs / stars are welcomed :)
