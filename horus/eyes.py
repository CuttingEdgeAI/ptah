import subprocess
import logging
import time
import sys
import logging

# Not totally convinced the -t option in ifstat does anything but in case one day it does...
INTERVAL = 5

logger = logging.getLogger(__name__)

class PacketEyeFedora:

    # Instantiate a bandwidth watcher. If there are less than min_rx_packets for max_rx_checks run by the check_traffic method, 
    # check_traffic returns false.
    def __init__(self, min_rx_packets=1, max_rx_checks=10, min_rx_bw=1024):
        self.min_rx_packets = min_rx_packets
        self.max_rx_checks = max_rx_checks
        self.min_rx_bw = min_rx_bw
        self.dead_rx_counter = 0

    def human_readable_to_bytes(self, size):
    #Given a human-readable byte string (e.g. 2G, 10GB, 30MB, 20KB),
    #return the number of bytes.  Will return 0 if the argument has
    #unexpected form.
        if (size[-1] == 'B'):
            size = size[:-1]
        if (size.isdigit()):
            bytes = int(size)
        else:
            bytes = size[:-1]
            unit = size[-1]
            if (bytes.isdigit()):
                bytes = int(bytes)
                if (unit == 'G'):
                    bytes *= 1073741824
                elif (unit == 'M'):
                    bytes *= 1048576
                elif (unit == 'K'):
                    bytes *= 1024
                else:
                    bytes = 0
            else:
                bytes = 0
        return bytes

    # Checks if there are incoming packets, if under threshold, return False, otherwise, True.
    def check_traffic(self):
        ifstat_result = subprocess.run(['ifstat',  '-t', str(INTERVAL), 'eth0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # logger.debug(ifstat_result)
        rx_packets = 0
        tx_packets = 0
        eth0_line = ifstat_result.stdout.decode('utf-8').split('\n')[3].strip()
        # logger.debug(eth0_line)
        try:
            rx_packets = int(eth0_line.split()[1])
            tx_packets = int(eth0_line.split()[3])
            rx_bw = self.human_readable_to_bytes(eth0_line.split()[5])
            tx_bw = self.human_readable_to_bytes(eth0_line.split()[7])
        except IndexError as e:
            logger.debug("Unable to detect rx packets, assuming 0")
            rx_packets = 0
        logger.debug("RX Packets {}, TX Packets {}, RX BW {}, TX BW {}".format(rx_packets, tx_packets, rx_bw, tx_bw))
        if rx_packets < self.min_rx_packets:
            self.dead_rx_counter += 1
            logger.debug("Low packets: Incrementing low rx dead counter. {}/{}".format(self.dead_rx_counter, self.max_rx_checks))
        elif rx_bw < self.min_rx_bw:
            self.dead_rx_counter += 1
            logger.debug("Low bandwidth: Incrementing low rx dead counter. {}/{}".format(self.dead_rx_counter, self.max_rx_checks))
        else:
            self.dead_rx_counter = 0
        if self.max_rx_checks > 0 and self.dead_rx_counter > self.max_rx_checks:
            logger.warning("Dead rx checks exceeded.")
            return False
        return True


def main():
    logging.basicConfig(level=logging.DEBUG)
    print("Running test with ifstat...")
    horus = PacketEyeFedora(1,3,100)

    while True:
        good = horus.check_traffic()
        if not good:
            break
        time.sleep(5)


if __name__ == '__main__':
    sys.exit(main())

