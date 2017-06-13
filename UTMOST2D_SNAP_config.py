from __future__ import division
import corr
import numpy as np
import matplotlib.pyplot as plt
import struct
import time

'''
This streamlines the SNAP configuration process.

This is the same as SNAP_spectrometer_config_with_pps.py (as of 8 June), but updated for the UTMOST firmware.

outline:
cell 1 -- imports

cell 2 -- This description

cell 3 -- Variables.  Ultimately these should be read from a configuration file.

cell 4 -- Defines functions

cell 5 -- Calls functions to configure the snap and packetizer

TODO:
--Maybe make the configuration variables, including gain/shift be read from a file.
--So far I've not done this because these rarely change, and when they do it's so far been easier to just edit them here, where their use and format is most clear.

'''
#---------------------- DEFINE CONFIGURATION PARAMETERS --------------------

PI_IP = '10.66.146.30' #string, IP of host raspberry pi
#BOFFILE  = 'spectrometer_new3_2016-11-14_1539.bof' #string, name of bof
BOFFILE  = 'spectrometer_new4_2017-2-6_1437.bof' #string, name of bof

SNAPID = 0xff #8 bit integer, identifies this particular snap board
SNAPMAC = 0x02020a000002 #48 bit integers, MAC for SNAP
SNAPIP  = 0x0a000002     # 32 bit integer, IP address of SNAP
SNAPPORT = 50000   #integer, port number to send from
DESTMACS = [0x0060DD46BFD9 for i in range(256)] #List of 256 48 bit integers, lists all possible destination MAC addresses
DESTINATION_IP_ADDRESSES = [0x0a000003]*10 #list of 32 bit integers, lists destination IP addresses in order of corresponding subbands
DESTINATION_PORTS = [50000]*10 #list of integers, lists destination ports in order of corresponding subbands

# Define band(s) to send
START_CHANNEL_1 = 330 # Lowest channel number of the set of 320 channels to send out the first ethernet port.
START_CHANNEL_2 = 10  # Lowest channel number of the set of 320 channels to send out the second ethernet port.

#---------------------DEFINE CONFIGURATION FUNCTIONS ----------------------

#def connect_to_snap(piip):
#    # connect to snap
#    r = corr.katcp_wrapper.FpgaClient(piip,7147)
#    time.sleep(2)
#    if r.is_connected():
#        print 'Connected to SNAP'
#    else:
#        print 'Not connected to SNAP'
#	exit()

def progfpga(name_of_bof):
    #load the bof
    if name_of_bof in r.listbof():
        print 'Found the boffile, now programming the FPGA.'
        print r.progdev(name_of_bof), 'done'
    else:
        print 'The raspberry pi does not have that boffile.'
	exit()
    time.sleep(1)
    status = r.read_int('ethernet_status')
    if status == 4:
        print 'ready to configure ethernet and packetizer'
    else:
        print "There's a problem, ethernet_status register = ", r.read_int('ethernet_status')
	if status <4:
		print "Status msb = 0 means that the ethernet link is not up." 
        exit()

def configurethernet():
    # configure ethernet
    print 'Configuring the 10Gb ethernet'
    r.config_10gbe_core('ten_Gbe_v2',SNAPMAC,SNAPIP,SNAPPORT,DESTMACS,gateway = 0)
    # Does it automatically iterate through mac addresses as IP changes?  How?
    print 'Configuring destination IP addresses and ports'
    for I in range(len(DESTINATION_IP_ADDRESSES)):
        ip = DESTINATION_IP_ADDRESSES[I]
        port = DESTINATION_PORTS[I]
        ipregister = 'tx_dest_ip%d' %I
        portregister = 'tx_dest_port%d' %I
        r.write_int(ipregister,ip)
        r.write_int(portregister,port)
    print 'done'

def resetandsync():
    #reset ethernet block and send sync pulse
    print 'Sending pulse to reset ethernet and sync.'
    r.write_int('force_new_sync',1)
    time.sleep(0.1)
    r.write_int('force_new_sync',0)
    print 'Done. Ethernet status = %d', r.read_int('ethernet_status')
    return

#----------------------CONFIGURE SNAP-------------------------

# Connect to SNAP
r = corr.katcp_wrapper.FpgaClient(PI_IP,7147)
time.sleep(2)
if r.is_connected():
    print 'Connected to SNAP'
else:
    print 'Not connected to SNAP'
    exit()

# load the boffile
progfpga(BOFFILE)
       
# set SNAP board identifier
r.write_int('pkt_header_SNAPid',SNAPID)

# configure ethernet
configurethernet()

#set reorder map

T = 8; #number of spectra per packet
Bt = 32; #TOTAL number of subbands in spectrum
B = 10; #number of subbands TO SEND
F = 32; #number of frequency channels per subband
M = 2; #number of modules per fft output stream
reorder_length = T*Bt*F*M;
# start = 330; #lowest frequency channel number to send
start1 = START_CHANNEL_1 + 2# in order to have it actually start on 330. TODO fix firmware so this offset isn't needed. It looks like a 2 clock cycle offset, or a one clock cycle offset and a difference in indexing convention (does something start on 0 and something else start on 1). 
start2 = START_CHANNEL_2 + 2
print "TODO: Fix in firmware the offset which is currently compensated for here."
I = np.ones(reorder_length);

reorder_length = T*Bt*F*M;

I = np.ones(reorder_length)

# Lines below were part of something useful for debugging
#m_test = np.zeros(reorder_length);
#b_test = np.zeros(reorder_length);
#f_test = np.zeros(reorder_length);
#t_test = np.zeros(reorder_length);
#p_test = np.ones(reorder_length);

j=0;
for b in range(B):
    for t in range(T):
        for f in range(F):
            for m in range(M):
                i1 = Bt*F*M*t + F*b +f + Bt*F*m + start1;
                i2 = Bt*F*M*t + F*b +f + Bt*F*m + start2;
                #p = m+f+b+t; This was useful for debugging. 
                I[2*j] = i1;
                I[2*j +1] = i2;
                j +=1;       
    j +=128; #defines gap between packets (gap between one set of subbands and the next)

reordermap = I.astype(int)
s = struct.Struct('>16384H')
r.write('reorder1_map1',s.pack(*reordermap))
time.sleep(0.1)

# reset ethernet and send sync pulse
resetandsync()

# Finish with a reminder to set the ADC demux
print "Now run 'python ~/adc16/adc16_init.py %s  -s -d 1 -g <adcgain>'" %(PI_IP + ' ' + BOFFILE)

print "Don't forget to adjust the digital gains"


