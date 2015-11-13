import random
import simpy
import math

RANDOM_SEED = None
SIM_TIME = 1000000
MU = 1



""" Queue system  """		
class server_queue:
	def __init__(self, env, arrival_rate, buffer_size, Packet_Delay, Server_Idle_Periods):
		self.server = simpy.Resource(env, capacity = 1)
		self.env = env
		self.queue_len = 0
		self.flag_processing = 0
		self.packet_number = 0
		self.sum_time_length = 0
		self.start_idle_time = 0
		self.arrival_rate = arrival_rate
		self.queue_capacity = buffer_size
		self.Packet_Delay = Packet_Delay
		self.Server_Idle_Periods = Server_Idle_Periods
		
	def process_packet(self, env, packet):
		with self.server.request() as req:
			start = env.now
			yield req
			yield env.timeout(random.expovariate(MU))
			latency = env.now - packet.arrival_time
			self.Packet_Delay.addNumber(latency)
			self.queue_len -= 1
			if self.queue_len == 0:
				self.flag_processing = 0
				self.start_idle_time = env.now
				
	def packets_arrival(self, env):
		# packet arrivals 
		
		while True:
		     # Infinite loop for generating packets
			yield env.timeout(random.expovariate(self.arrival_rate))
			  # arrival time of one packet

			self.packet_number += 1
			  # packet id
			arrival_time = env.now  

			if self.queue_len < self.queue_capacity:
				#print(self.num_pkt_total, "packet arrival")
				new_packet = Packet(self.packet_number,arrival_time)
				if self.flag_processing == 0:
					self.flag_processing = 1
					idle_period = env.now - self.start_idle_time
					self.Server_Idle_Periods.addNumber(idle_period)
					#print("Idle period of length {0} ended".format(idle_period))

				self.queue_len += 1
				env.process(self.process_packet(env, new_packet))
			else:
				self.Packet_Delay.addDroppedPacket()


""" Packet class """			
class Packet:
	def __init__(self, identifier, arrival_time):
		self.identifier = identifier
		self.arrival_time = arrival_time
		

class StatObject:
    def __init__(self):
        self.dataset =[]
        self.dropped_packets = 0

    def addNumber(self,x):
        self.dataset.append(x)
    def count(self):
    	return len(self.dataset)
    def addDroppedPacket(self):
    	self.dropped_packets += 1
    def packetLossProbability(self):
    	return float(self.dropped_packets) / self.total() # float to stop int trucation
    def total(self):
    	return len(self.dataset) + self.dropped_packets

def expectedLossProbability(arrival_rate, buffer_size):
	return 1 - ( float(math.pow(arrival_rate, buffer_size + 1) - 1) / (math.pow(arrival_rate, buffer_size + 2) - 1) )

def main():
	print("Simple queue system model: mu = {0}".format(MU))
	print ("{0:<10} {1:<9} {2:<9} {3:<9} {4:<16} {5:<16} {6:<13} {7:<13}".format(
        "BufferSize", "Lambda", "Total", "Processed", "SimulatedDropped", "ExpectedDropped", "SimulatedPd", "ExpectedPd"))
	random.seed(RANDOM_SEED)
	for B in [10, 50]:
		for arrival_rate in [0.2, 0.4, 0.6, 0.8, 0.9, 0.99]:
			env = simpy.Environment()
			Packet_Delay = StatObject()
			Server_Idle_Periods = StatObject()
			router = server_queue(env, arrival_rate, B, Packet_Delay, Server_Idle_Periods)
			env.process(router.packets_arrival(env))
			env.run(until=SIM_TIME)
			expected_dropped = int(expectedLossProbability(arrival_rate, B) * Packet_Delay.total())
			print ("{0:<10} {1:<9.3f} {2:<9} {3:<9} {4:<16} {5:<16} {6:<13.8f} {7:<13.8f}".format(
				B,
				round(arrival_rate, 3),
				int(Packet_Delay.total()),
				int(Packet_Delay.count()),
				int(Packet_Delay.dropped_packets),
				expected_dropped,
				round(Packet_Delay.packetLossProbability(), 8),
				round(expectedLossProbability(arrival_rate, B), 8)
			))
	
if __name__ == '__main__': main()


