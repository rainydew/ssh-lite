#!/usr/bin/env python
# coding: utf-8
# author: Rainy Chan
# mailto: rainydew@qq.com
import paramiko
import threading
import time
import sys
import warnings


class KeyAbbr:
    """alias of combination keys"""
    CTRL_C = "\x03"
    CTRL_D = "\x04"
    CTRL_Z = "\x1a"


class Server(object):
    """a simple server that is easy to use"""
    def __init__(self, hostname, password=None, username="root", port=22, key_path=None, timeout=10, debug=False,
                 debug_file=sys.stdout, disable_warnings=False):
        """
        create a connection to a remote server
        use "del connection_variable" to disconnect
        it will try both ssh and sftp. if sftp is disallowed, it will continue with a warning
        :param str hostname: ip or internet address to connect
        :param int port: the ssh service port (firewall should accept)
        :param key_path: set it to the path of key file if server needs rsa key to auth
        :param bool debug: set it to True if you want to see realtime server input and output
        :param file debug_file: set a file/pipe obj (text mode) to write debug. NOTE this file will NOT close automatically
        """
        chan = paramiko.SSHClient()
        pkey = paramiko.RSAKey.from_private_key(open(key_path, 'r')) if key_path else None
        chan.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        chan.connect(hostname, port, username, password, pkey, timeout=timeout)
        tp = paramiko.Transport(sock=(hostname, port))
        tp.connect(username=username, password=password, pkey=pkey)
        self._disable_warnings = disable_warnings
        try:
            ftp = paramiko.SFTPClient.from_transport(tp)
        except:
            if not self._disable_warnings:
                warnings.warn("WARNING ftp connect failed of {}, set to None\n".format(hostname))
            self._ftp = None
        else:
            self._ftp = ftp
        self.chan = chan  # ssh client
        self.ssh = chan.invoke_shell()  # type: paramiko.channel.Channel
        self._reading = False
        self._buff = b""
        self.last_recv = None  # time of last receiving bytes
        self.debug = debug
        self._debug_file = debug_file
        t = threading.Thread(target=self._block_data)
        t.setDaemon(True)
        t.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ssh.close()
        self.chan.close()
        if self._ftp:
            self._ftp.close()

    def put_file(self, local, remote):
        """
        push a file to server
        :param str local: local filepath + filename
        :param str remote: server filepath + filename
        """
        if self._ftp:
            self._ftp.put(local, remote)
        else:
            raise IOError("Cannot put file since ftp of this session is unavailable")

    def get_file(self, remote, local):
        """
        download a file from server
        :param str remote: server filepath + filename
        :param str local: local filepath [ + filename ]
        """
        if self._ftp:
            self._ftp.get(remote, local)
        else:
            raise IOError("Cannot get file since ftp of this session is unavailable")

    def send(self, cmd, end='\n'):
        """
        send seq of characters without wait
        :param end: default to enter (\n), however when sending combination keys
        """
        self.ssh.send(cmd + end)

    def _block_data(self):
        while 1:
            res = self.ssh.recv(4096)
            if not res:
                break
            self._buff += res
            self.last_recv = time.time()
            if self.debug:
                self._debug_file.write(res)
                self._debug_file.flush()

    def send_and_read(self, cmd, end='\n', timeout=3):
        """
        send seq of characters, wait for `timeout` seconds then return all buffering outputs
        to remove buffering outputs before sending this command, use `get_buff` method first
        this method will clear the buff
        :param timeout: sleep time after sending the message
        :return str: all above outputs at `timeout` time point
        """
        for i in range(3):
            if self._reading:
                time.sleep(5)
            else:
                break
        else:
            raise RuntimeError("cannot send msg to a busy pipe")

        self._buff = b""
        self.send(cmd, end)
        self.last_recv = time.time()
        self._reading = True
        while time.time() - self.last_recv < timeout:
            time.sleep(0.1)
        buff = self._buff
        self._buff = b""
        self._reading = False
        return buff

    def expect(self, pat, timeout=15, failpat=None, success_info=False):
        """
        block until `pat` (or any item in `pat` if `pat` is a list) is found in buffer outputs
        if `timeout` reaches zero first, it will raise an AssertionError
        this method will clear the buff
        :param Union[str, List[str]] pat: the single string or a string list to wait
        :param Union[None, str, List[str]] failpat: raise an AssertionError if failpat set and was found in output before `pat` was found
        :param bool success_info: whether to print info if `pat` is found
        :return str: all above outputs ended with line that includes `pat`
        """
        assert type(pat) in (unicode, str, list), "unsupported type"
        s = time.time()
        self._check_fail(failpat)
        if type(pat) != list:
            while pat not in self._buff:
                time.sleep(0.1)
                self._check_fail(failpat)
                if timeout:
                    assert s + timeout >= time.time(), "expect timeout"
        else:
            while all([x not in self._buff for x in pat]):
                time.sleep(0.1)
                self._check_fail(failpat)
                if timeout:
                    assert s + timeout >= time.time(), "expect timeout"
        res = self._buff
        self._buff = b""
        if success_info:
            sys.stdout.write("\nexpect {} success\n".format(pat))
            sys.stdout.flush()
        return res

    def get_buff(self, clear_buff=True):
        """
        get current outputs
        you can use this method only for clear buff by just call get_buff()
        :param bool clear_buff: whether clear the buff after calling it
        :return str: all current outputs in buff
        """
        b = self._buff
        if clear_buff:
            self._buff = b""
        return b

    @staticmethod
    def grep(instr, pattern, reverse=False):
        """
        filter that includes or excludes `pattern` of the `instr` block
        """
        return [found.strip() for found in (instr if type(instr) == list else instr.split("\n")) if
                (pattern in found if not reverse else pattern not in found)]

    def __del__(self):
        """
        disconnect
        """
        try:
            self.ssh.close()  # to stop blockData
        except:
            pass
        try:
            self.chan.close()
        except:
            pass
        if self._ftp:
            try:
                self._ftp.close()
            except:
                pass

    def _check_fail(self, failpat):
        if failpat is not None:
            if type(failpat) == str:
                if failpat in self._buff:
                    raise AssertionError("fail pattern {} found".format(failpat))
            else:
                if any([x in self._buff for x in failpat]):
                    raise AssertionError("a fail pattern of {} found".format(failpat))