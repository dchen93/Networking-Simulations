# Daniel Chen (997415944) & Ittai Shay (998099673)
# ECS 152A - Ghosal
# 7 December 2015
# Project Part 2

import matplotlib.pyplot as pyplot
import random
import simpy
import math

SIM_TIME = 1000000
SLOT_RATE = 1
NUM_HOSTS = 10

slot_number = 0

class ethernet_system:
    def __init__(self, env, slot_period, host_queues):
        self.env = env
        self.slot_period = slot_period # time to next slot
        self.hosts = host_queues
        self.processed_packets = 0 # number of processed packets
        self.collisions = 0 # number of slots that experienced a collision

        # now we add the NUM_HOSTS host queue packet arrival simulation threads
        for i in range(NUM_HOSTS):
            env.process(self.hosts[i].packets_arrival(self.env))

    def run_system(self,env):
        global slot_number
        while True:
            # figure out which queues want to transmit in this slot
            counter = 0
            index = []
            for i in range(NUM_HOSTS):
                if self.hosts[i].slot_target == slot_number:
                    counter += 1
                    index.append(i)

            if counter > 1: # multiple queues want to transmit, handle collisions
                self.collisions += 1
                for i in index:
                    self.hosts[i].collision_backoff()
            elif counter == 1: # only one queue wants to transmit, process that packet
                self.hosts[index[0]].send_packet()
                self.processed_packets += 1

            yield env.timeout(self.slot_period)
            slot_number += 1 # move to the next slot

""" Queue system  """       
class host_queue:
    def __init__(self, env, arrival_rate, exponential):
        self.env = env
        self.queue_len = 0 # size of the queue (number of pending packets)
        self.arrival_rate = arrival_rate
        self.failures = 0 # number of failures/collisions the packet at the front of the queue has experienced
        self.slot_target = 0 # which slot the queue will try to transmit the packet at the front of the queue
        self.exponential = exponential # whether to use exponential backoff or linear backoff

    def packets_arrival(self, env):
        # packet arrivals 
        while True:
            # Infinite loop for generating packets
            yield env.timeout(random.expovariate(self.arrival_rate))

            # set target slot for first pending packet if queue was empty
            if self.queue_len == 0:
                self.reset_target()

            self.queue_len += 1

    # called when the pending packet collides while trying to process 
    def collision_backoff(self):
        if self.exponential:
            self.slot_target += random.randint(0,2**min(self.failures, 10)) + 1
        else:
            self.slot_target += random.randint(0,min(self.failures, 1024)) + 1

        self.failures += 1

    # update queue once packet at the front gets processed by ethernet_system
    def send_packet(self):
        self.queue_len -= 1
        if self.queue_len > 0: # update the slot target and failures for the next packet
            self.reset_target()

    def reset_target(self):
        global slot_number
        self.slot_target = slot_number + 1 # target the next slot initially
        self.failures = 0 # reset failures/collisions to 0

def main():
    global slot_number
    print("Random Access Protocol Simulation")
    for exponential in [True, False]:
        pyplot.clf() # clear plot
        if exponential:
            print("Exponential Backoff")
        else:
            print("Linear Backoff")

        print("{0:<9} {1:<12} {2:<9} {3:<9} {4:<9}".format(
            "Lambda", "Throughput", "Processed", "Slots", "Collisions"))

        x = [] # x axis will hold lambda
        y = [] # y axis will hold throuhput

        for arrival_rate in [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]:
            slot_number = 0 # reset slot number for each new lambda
            env = simpy.Environment()
            host_queues = [host_queue(env, arrival_rate, exponential) for i in range(NUM_HOSTS)] 
            ethernet = ethernet_system(env, SLOT_RATE, host_queues)
            env.process(ethernet.run_system(env))
            env.run(until=SIM_TIME)

            throughput = round(float(ethernet.processed_packets) / slot_number, 5)
            x.append(arrival_rate)
            y.append(throughput)

            print("{0:<9.3f} {1:<12.5f} {2:<9} {3:<9} {4:<9}".format(
                round(arrival_rate,3),
                throughput,
                ethernet.processed_packets,
                slot_number,
                ethernet.collisions
            ))


        pyplot.axis([0, 0.1, 0, 1])    
        pyplot.xticks([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09])
        pyplot.yticks([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
        pyplot.xlabel('Lambda')
        pyplot.ylabel('Throughput')
        pyplot.plot(x,y, color='blue', marker='o')

        for i in range(9):
            pyplot.annotate(s = str(y[i]), xy = (x[i], y[i]), xycoords='data', rotation=90, textcoords='offset points', xytext=(-5, 50))

        if exponential:
            pyplot.title('Exponential Backoff: Lambda vs Throughput')
            pyplot.savefig('exponential.png')
        else:
            pyplot.title('Linear Backoff: Lambda vs Throughput')
            pyplot.savefig('linear.png')
    
if __name__ == '__main__': main()