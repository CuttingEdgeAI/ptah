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
    def __init__(self, min_rx_packets=1, max_rx_checks=10):
        self.min_rx_packets = min_rx_packets
        self.max_rx_checks = max_rx_checks
        self.dead_rx_packets_counter = 0

    # Checks if there are incoming packets, if under threshold, return False, otherwise, True.
    def check_traffic(self):
        logger.info("Checking traffic")
        ifstat_result = subprocess.run(['ifstat',  '-t', str(INTERVAL), 'eth0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # logger.debug(ifstat_result)
        rx_packets = 0
        tx_packets = 0
        try:
            rx_packets = int(ifstat_result.stdout.decode('utf-8').split('\n')[3].strip().split()[1])
            tx_packets = int(ifstat_result.stdout.decode('utf-8').split('\n')[3].strip().split()[3])
        except IndexError as e:
            logger.debug("Unable to detect rx packets, assuming 0")
            rx_packets = 0
        logger.debug("RX Packets {}, TX Packets {}".format(rx_packets, tx_packets))
        if rx_packets < self.min_rx_packets:
            self.dead_rx_packets_counter += 1
            logger.debug("Incrementing low rx dead counter. {}/{}".format(self.dead_rx_packets_counter, self.max_rx_checks))
        else:
            self.dead_rx_packets_counter = 0
        if self.dead_rx_packets_counter > self.max_rx_checks:
            logger.warning("Dead packet checks exceeded.")
            return False
        return True


def main():
    logging.basicConfig(level=logging.DEBUG)
    print("Running test with ifstat...")
    horus = PacketEyeFedora(10,3)

    while True:
        good = horus.check_traffic()
        if not good:
            break
        time.sleep(5)


if __name__ == '__main__':
    sys.exit(main())

