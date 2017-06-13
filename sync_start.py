import time
reference = time.time()
import corr
import socket
from argparse import ArgumentParser
import sys

#Parse command line arguments
p = ArgumentParser(description = 'python sync_start.py rpi [OPTIONS]')
p.add_argument('rpi', type = str, default = '', help = 'specify the ip address of the raspberry pi which is connected to the SNAP')
#p.add_argument('-v', '--verbose', dest = '?', type = int , default = 2**5, help = 'Digital gain for the post-pfb requantization.')
#TODO make all the printed timestamps only happen for verbose option.
#print 'corr imported, time since reference = ', (time.time() - reference)


args = p.parse_args()
rpi = args.rpi

#Connect to SNAP
r = corr.katcp_wrapper.FpgaClient(rpi,7147)
#time.sleep(0.0005) This is somehwat more than what I'd found to be the minimum wait time but sometimes it's not enough.
time.sleep(0.6)
#time.sleep(1.)
if r.is_connected():
    #print 'Connected to SNAP'
    pass
else:
    print 'Not connected to SNAP'
    exit()

#print 'connected to SNAP, time since reference = ', (time.time() - reference)

r.write_int('software_start',0) # This is so that this register is definitely zero, since triggering a start requires a rising edge detect.

#print 'wrote software_start to 0, time since reference =', (time.time() - reference)

#open a socket that will be used to send a timestamp to bf08
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET is the address/protocol type and SOCK_STREAM is the socket type
sock.connect(('mpsr-bf08',5000))

#print 'socket opened'

#----------------------BEGIN Precisely timed steps.--------------------------

now  = time.strftime('%Y_%m_%d_%H:%M:%S',time.gmtime())  #find out what time it is
yet = (time.strftime('%Y_%m_%d_%H:%M:%S',time.gmtime()) != now)
#print now

while not yet: #wait until a second boundary
	go = time.strftime('%Y_%m_%d_%H:%M:%S',time.gmtime())
	yet = (go != now)

data_go = time.strftime('%Y-%m-%d-%H:%M:%S',time.gmtime(time.time()+1)) # timestamp for when data will start
		
time.sleep(0.5) #wait 500 ms after the boundary
r.write_int('software_start',1) #tell the SNAP to start on the next pulse

#print go
print data_go 
for_bf08 = data_go + '\r\n'
sock.sendall(for_bf08) # tell BF08 what time SNAP will start.

#----------------------END Precisely timed steps.----------------------------

time.sleep(1)
r.write_int('software_start',0)

sock.close() #close the socket
#print 'all done, time since reference = ', (time.time() - reference)
exit()
