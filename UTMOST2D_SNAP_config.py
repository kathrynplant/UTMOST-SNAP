'''
This streamlines the SNAP configuration process.

This is the same as SNAP_spectrometer_config_with_pps.py (as of 8 June), but updated for the UTMOST firmware.

outline:
1. imports

2. Parse arguments.

3. Defines parameters from a configuration file.

4. Defines functions

5. Calls functions to configure the snap and packetizer

TODO:
--Maybe include setting gain and shift. Currently that's done separately.

'''
from __future__ import division
import corr
import numpy as np
import matplotlib.pyplot as plt
import struct
import time
import sys

#---------------------- DEFINE CONFIGURATION PARAMETERS --------------------
# def line parser
def lineparse(line):
    for i in range(len(line)):
        if line[i] == '=':
            keysplit = line[:i]
            valsplit = line[(i+1):]
            key = keysplit.strip()
            value = valsplit.strip()
    return key , value

# load config file
configfile = r'sampleconfig_UTMOST2D.txt'
print 'Using config file', configfile
with open(configfile) as f:
    raw = f.readlines()
lines = [x.strip() for x in raw]
textlines = [x for x  in lines if ((len(x) > 0) and (x[0] != '#'))]

# make dictionary of parameter keywords and their values
paramdict = {}
fails = 0
for line in textlines:
    key, value = lineparse(line)
    try:
        paramdict[key] = eval(value)
    except:
        print 'Could not evaluate', key, ' ', value
        print sys.exc_info()[1]
        fails +=1
if fails > 0:
    print 'Failed parsing config parameters.  Please correct the config file.'
    exit()

# Check that all the necessary parameters have been included, and no invalid parameters have been included.
valid = ['PI_IP', 
         'BOFFILE', 
         'SNAPID', 
         'SNAPMAC', 
         'SNAPIP1',
         'SNAPIP2',
         'SNAPPORT1',
         'SNAPPORT2',
         'DESTMACS1',
         'DESTMACS2',
         'DESTINATION_IP_ADDRESSES',
         'DESTINATION_PORTS',
         'START_CHANNEL_1',
         'START_CHANNEL_2']
invalidcount = 0
missingcount = 0
for k in valid:
    if k not in paramdict.keys():
        print 'Missing ', k, ' please add it to the config file.'
        missingcount +=1
for k in paramdict.keys():
    if k not in valid:
        print 'Invalid parameter', k
        invalidcount+=1
if (invalidcount + missingcount) > 0:
    print 'Please make sure that you\'re using a config file which includes all of these parameters and only these parameters:'
    print valid
    exit()

# Define variables
PI_IP = paramdict['PI_IP'] #string, IP of host raspberry pi
BOFFILE = paramdict['BOFFILE'] #string, name of bof
SNAPID = paramdict['SNAPID']        #8 bit integer, identifies this particular snap board
SNAPMAC = paramdict['SNAPMAC']      #48 bit integers, MAC for SNAP
SNAPIP1  = paramdict['SNAPIP1']     # 32 bit integer, IP address of SNAP
SNAPIP2  = paramdict['SNAPIP2']     # 32 bit integer, IP address of SNAP
SNAPPORT1 =paramdict['SNAPPORT1']   #integer, port number for ethernet1 to send from
SNAPPORT2 = paramdict['SNAPPORT2']  #integer, port number for ethernet2 to send from
DESTMACS1 = paramdict['DESTMACS1']  #List of 256 48 bit integers, lists all destination MAC addresses for ethernet1.
DESTMACS2 = paramdict['DESTMACS2']  #List of 256 48 bit integers, lists all destination MAC addresses for ethernet2.
DESTINATION_IP_ADDRESSES = paramdict['DESTINATION_IP_ADDRESSES'] #list of 32-bit integers, lists destination IP addresses in order of corresponding subbands. The first 10 are for ethernet1, the last 10 for ethernet2.
DESTINATION_PORTS =  paramdict['DESTINATION_PORTS'] #list of integers, lists destination ports in order of corresponding subbands. The first 10 are for ethernet 1, the last 10 are for ethernet 2.
START_CHANNEL_1 = paramdict['START_CHANNEL_1'] # Lowest channel number of the set of 320 channels to send out the first ethernet port.
START_CHANNEL_2 = paramdict['START_CHANNEL_2']  # Lowest channel number of the set of 320 channels to send out the second ethernet port.

#---------------------DEFINE CONFIGURATION FUNCTIONS ----------------------

def progfpga(name_of_bof):
    #load the bof
    if name_of_bof in r.listbof():
        print 'Found the boffile, now programming the FPGA.'
        print r.progdev(name_of_bof), 'done'
    else:
        print 'The raspberry pi does not have that boffile.'
	exit()
    time.sleep(1)
    status1 = r.read_int('ethernet1_status')
    status2 = r.read_int('ethernet2_status')
    if (status1 == 4) and (status2 == 4):
        print 'ready to configure ethernet and packetizer'
    
    elif status1 != 4:
        print "There's a problem, ethernet1 status register = ", r.read_int('ethernet1_status')
	if status1 <4:
		print "Status msb = 0 means that the ethernet link is not up." 
        exit()
    
    elif status2 != 4:
        print "There's a problem, ethernet2 status register = ", r.read_int('ethernet2_status')
	if status2 <4:
		print "Status msb = 0 means that the ethernet link is not up." 
        exit()

def configurethernet():
    # configure ethernet
    print 'Configuring the 10Gb ethernet'
    r.config_10gbe_core('gbe1',SNAPMAC,SNAPIP1,SNAPPORT1,DESTMACS1,gateway = 0)
    r.config_10gbe_core('gbe2',SNAPMAC,SNAPIP2,SNAPPORT2,DESTMACS2,gateway = 0)

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
    print 'Ethernet1 status = ', r.read_int('ethernet1_status')
    print 'Ethernet2 status = ', r.read_int('ethernet2_status')
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
print 'Done.'

# Finish with a reminder to set the ADC demux
print "Next, calibrate the ADCs with Zuhra's script. Run: \n 'python ~/adc16/adc16_init.py %s  -s -d 1 -g <adcgain>'" %(PI_IP + ' ' + BOFFILE)

print "Don't forget to adjust the digital gains using set_gain.py."


