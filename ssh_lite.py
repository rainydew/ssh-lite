#!/usr/bin/env python3
# coding: utf-8
# author: Rainy Chan
# mailto: rainydew@qq.com
from typing import Optional, Union, List
import paramiko
import threading
import time
import sys


class KeyAbbr:
    """alias of combination keys"""
    CTRL_C = "\x03"
    CTRL_D = "\x04"


class Server(object):
    """a simple server that is easy to use"""
    def __init__(self, hostname: str, password: Optional[str] = None, username: str = "root", port: int = 22,
                 key_path: Optional[str] = None, timeout: int = 10):
        chan = paramiko.SSHClient()
        pkey = paramiko.RSAKey.from_private_key(open(key_path, 'r')) if key_path else None
        chan.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        chan.connect(hostname, port, username, password, pkey, timeout=timeout)
        tp = paramiko.Transport(sock=(hostname, port))
        tp.connect(username=username, password=password, pkey=pkey)
        ftp = paramiko.SFTPClient.from_transport(tp)
        self.ftp = ftp
        self.chan = chan
        self.ssh = chan.invoke_shell()  # type: paramiko.channel.Channel
        self.reading = False
        self.buff = b""
        self.last_recv = None
        self.debug = False
        t = threading.Thread(target=self._block_data)
        t.setDaemon(True)
        t.start()

    def put_file(self, local: str, remote: str):
        self.ftp.put(local, remote)

    def get_file(self, remote: str, local: str):
        self.ftp.get(remote, local)

    def send(self, cmd: str, end: str = '\n'):
        cmd = (cmd + end).encode("utf-8")
        self.ssh.send(cmd)

    def _block_data(self):
        while 1:
            res = self.ssh.recv(64)
            if not res:
                break
            self.buff += res
            self.last_recv = time.time()
            if self.debug:
                sys.stdout.buffer.write(res)
                sys.stdout.flush()

    def send_and_read(self, cmd: str, end: str = '\n', timeout: int = 3) -> str:
        for i in range(3):
            if self.reading:
                time.sleep(5)
            else:
                break
        else:
            raise TimeoutError("cannot send msg to a busy pipe")

        self.buff = b""
        self.send(cmd, end)
        self.last_recv = time.time()
        self.reading = True
        while time.time() - self.last_recv < timeout:
            time.sleep(0.1)
        buff = self.buff
        self.buff = b""
        self.reading = False
        return buff.decode("utf-8", errors="replace")

    def expect(self, pat: Union[str, List[str]], timeout: int = 15, clear_buff: bool = True):
        assert type(pat) in (str, list), "unsupported type"
        pat_b = pat.encode("utf-8") if type(pat) != list else [x.encode('utf-8') for x in pat]
        s = time.time()
        if type(pat_b) != list:
            while pat_b not in self.buff:
                time.sleep(0.1)
                if timeout:
                    assert s + timeout >= time.time(), "expect timeout"
        else:
            while all([x not in self.buff for x in pat_b]):
                time.sleep(0.1)
                if timeout:
                    assert s + timeout >= time.time(), "expect timeout"
        if clear_buff:
            self.buff = b""
        sys.stdout.write("\nexpect {} success\n".format(pat))
        sys.stdout.flush()

    def get_buff(self, clear_buff: bool = True) -> str:
        b = self.buff
        if clear_buff:
            self.buff = b""
        return b.decode("utf-8", errors="replace")

    @staticmethod
    def grep(instr: Union[str, List[str]], pattern: str, reverse: bool = False) -> List[str]:
        return [found.strip() for found in (instr if type(instr) == list else instr.split("\n")) if
                (pattern in found if not reverse else pattern not in found)]

    def __del__(self):
        self.ssh.close()  # to stop blockData
        self.chan.close()
        self.ftp.close()
