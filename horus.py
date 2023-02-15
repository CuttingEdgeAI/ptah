#!/usr/bin/env python3

from subprocess import Popen, PIPE
import shlex
import time
import sys
from threading import Thread
import logging

ON_POSIX = 'posix' in sys.builtin_module_names

logger = logging.getLogger('__horus__')
logger.setLevel(logging.INFO)


class Horus:
    last_std_msg_time = time.time()
    cmd = ''
    quiet_timeout_seconds = 0
    timeout_seconds = None
    proc = None
    start_time = time.time()
    poison_pilled = False

    def __init__(self, cmd, quiet_timeout_seconds, timeout_seconds=None, poison_pills=[], log_blacklist=[]):
        self.cmd = cmd
        self.quiet_timeout_seconds = quiet_timeout_seconds
        self.timeout_seconds = timeout_seconds
        self.poison_pills = poison_pills
        self.log_blacklist = log_blacklist
        self.start()

    def print_if_not_blacklisted(self, line):
        if len(self.log_blacklist) == 0:
                print(line)
        else:
            blacklisted = False
            for black_line in self.log_blacklist:
                if black_line in line:
                    blacklisted = True
            if blacklisted is False:
                print(line)       


    def enqueue_output(self, out):
        logger.info("Output thread ready for {}".format(out))
        for line in iter(out.readline, b''):
            # print("Readline: {}, from {}".format(line.decode(), out))
            decoded_line = line.decode().rstrip('\n')
            self.print_if_not_blacklisted(decoded_line)
            for pill in self.poison_pills:
                if pill in decoded_line:
                    logger.warning("Poison pill detected.")
                    self.poison_pilled = True
            self.last_std_msg_time = time.time()
        logger.debug("Closing thread {}".format(out))
        out.close()


    def start(self):
        logger.info("Starting command {}".format(self.cmd))
        logger.info("Quiet Timeout {}".format(self.quiet_timeout_seconds))
        self.proc = Popen(self.cmd, shell=False, stdout=PIPE, stderr=PIPE, bufsize=0, close_fds=ON_POSIX)
        t_so = Thread(target=self.enqueue_output, args=(self.proc.stdout,))
        t_se = Thread(target=self.enqueue_output, args=(self.proc.stderr,))
        t_so.daemon = True
        t_se.daemon = True
        t_so.start()
        t_se.start()


    def poll(self):
        quiet_diff = time.time() - self.last_std_msg_time
        logger.debug("Time since last message {}".format(quiet_diff))
        runtime_diff = time.time() - self.start_time
        logger.debug("Time since startup {}".format(runtime_diff))
        p_retcode = self.proc.poll()
        if self.poison_pilled:
            logger.warning("Observed poisoned state, shutting down.")
            self.proc.terminate()
            self.proc.kill()
            return self.proc.poll()
        if p_retcode is not None:
            logger.debug("cmd {} is dead, shutting down, return code: {}".format(self.cmd, p_retcode))
            self.proc.terminate()
            return p_retcode
        if self.quiet_timeout_seconds > 0 and quiet_diff > self.quiet_timeout_seconds:
            logger.warning("No log message in {} seconds, terminating command {}".format(quiet_diff, self.cmd))
            self.proc.terminate()
            self.proc.kill()
            return self.proc.poll()
        if self.timeout_seconds and (runtime_diff > self.timeout_seconds):
            logger.warning("Command took longer than horus timeout, terminating command {}".format(runtime_diff, self.cmd))
            self.proc.terminate()
            self.proc.kill()
            return self.proc.poll()
        return self.proc.poll()

    def terminate(self):
        self.proc.terminate()
                            

def main():
    print("Running test with ping...")
    # cmd = './ghost-app -c config/ghost-config-camera-steve.txt'
    cmd = 'ping -i 1 127.0.01'
    # cmd = 'ls'
    horus = Horus(shlex.split(cmd), 5, 10, log_blacklist=[], poison_pills=['bytes', 'lol'])

    while True:
        retcode = horus.poll()
        if retcode is not None:
            break
        time.sleep(5)


if __name__ == '__main__':
    sys.exit(main())