#!/usr/bin/env python3

from subprocess import Popen, PIPE
import shlex
import time
import sys
from threading import Thread
import logging
import os

ON_POSIX = 'posix' in sys.builtin_module_names

logger = logging.getLogger(__name__)


class Ptah:


    def __init__(self, cmd, quiet_timeout_seconds, timeout_seconds=None, poison_pills=[], log_blacklist=[],
                 start_delay=0, good_pills=[], good_pill_timeout_seconds=-1, custom_env_vars=None):
        self.cmd = cmd
        self.last_std_msg_time = time.time()
        self.last_good_pill_time = time.time()
        self.start_time = time.time()
        self.quiet_timeout_seconds = int(quiet_timeout_seconds)
        self.good_pill_timeout_seconds = int(good_pill_timeout_seconds)
        self.timeout_seconds = int(timeout_seconds)
        self.poison_pills = poison_pills
        self.good_pills = good_pills
        self.log_blacklist = log_blacklist
        self.start_delay = int(start_delay)
        self.poison_pilled = False
        self.blacklist_counter = 0
        self.custom_env_vars = custom_env_vars if custom_env_vars is not None else os.environ.copy()
        if len(good_pills) > 0 and self.good_pill_timeout_seconds <= 0:
            logger.error("If good pill list is defined, good_pill_timeout_seconds must be > 0")
            sys.exit(1)

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
            else:
                self.blacklist_counter += 1

    # Return True if line is a good pill
    def is_good_pill(self, line):
        # If no good pills defined, everything is good
        if len(self.good_pills) == 0:
            return True
        else:
            for good_pill in self.good_pills:
                if good_pill in line:
                    return True
            return False
                

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
            if self.is_good_pill(decoded_line):
                self.last_good_pill_time = time.time()
        logger.debug("Closing thread {}".format(out))
        out.close()


    def start(self):
        logger.info("Quiet Timeout {}".format(self.quiet_timeout_seconds))
        logger.info("Poison Pills {}".format(self.poison_pills))
        logger.info("Good Pills {}".format(self.good_pills))
        logger.info("Good Pills Timeout (s) {}".format(self.good_pill_timeout_seconds))
        logger.info("Timeout {}".format(self.timeout_seconds))
        logger.info("Log Blacklist {}".format(self.log_blacklist))
        logger.info("Start Delay {}".format(self.start_delay))
        logger.info("Starting command {}".format(self.cmd))
        if self.start_delay > 0:
            logger.info("Delaying start by {}.".format(self.start_delay))
            time.sleep(self.start_delay)
        self.proc = Popen(self.cmd, shell=False, stdout=PIPE, stderr=PIPE, bufsize=0, close_fds=ON_POSIX, env=self.custom_env_vars)
        t_so = Thread(target=self.enqueue_output, args=(self.proc.stdout,))
        t_se = Thread(target=self.enqueue_output, args=(self.proc.stderr,))
        t_so.daemon = True
        t_se.daemon = True
        t_so.start()
        t_se.start()


    def poll(self):
        quiet_diff = time.time() - self.last_std_msg_time
        good_pill_diff = time.time() - self.last_good_pill_time
        # logger.debug("Time since last message {}".format(quiet_diff))
        runtime_diff = time.time() - self.start_time
        # logger.debug("Time since startup {}".format(runtime_diff))
        p_retcode = self.proc.poll()
        logger.debug("{} blacklisted log messages observed since last poll.".format(self.blacklist_counter))
        self.blacklist_counter = 0
        if self.poison_pilled:
            logger.warning("Observed poisoned state, shutting down.")
            self.proc.terminate()
            self.proc.kill()
            return self.proc.poll()
        if p_retcode is not None:
            logger.debug("cmd {} is dead, shutting down, return code: {}".format(self.cmd, p_retcode))
            self.proc.terminate()
            return p_retcode
        if self.quiet_timeout_seconds and self.quiet_timeout_seconds > 0 and quiet_diff > self.quiet_timeout_seconds:
            logger.warning("No log message in {} seconds, terminating command {}".format(quiet_diff, self.cmd))
            self.proc.terminate()
            self.proc.kill()
            return self.proc.poll()
        if self.timeout_seconds and self.timeout_seconds > 0 and (runtime_diff > self.timeout_seconds):
            logger.warning("Command took longer than ptah timeout {}, terminating command {}".format(self.timeout_seconds, self.cmd))
            self.proc.terminate()
            self.proc.kill()
            return self.proc.poll()
        if self.good_pill_timeout_seconds and self.good_pill_timeout_seconds > 0 and (good_pill_diff > self.good_pill_timeout_seconds):
            logger.warning("No good pill log message in {} seconds, terminating command {}".format(good_pill_diff, self.cmd))
            self.proc.terminate()
            self.proc.kill()
            return self.proc.poll()
        return self.proc.poll()

    def terminate(self):
        self.proc.terminate()
                            

def main():
    logging.basicConfig(level=logging.DEBUG)
    print("Running test with ping...")
    cmd = 'ping -i 1 127.0.01'
    ptah = Ptah(shlex.split(cmd), quiet_timeout_seconds=5, timeout_seconds=15, log_blacklist=['bytes'], 
                  poison_pills=['lol'], start_delay=2, good_pills=[], good_pill_timeout_seconds=5)

    while True:
        retcode = ptah.poll()
        if retcode is not None:
            break
        time.sleep(5)


if __name__ == '__main__':
    sys.exit(main())