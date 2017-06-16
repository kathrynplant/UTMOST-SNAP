from __future__ import division
import corr
import numpy as np
import matplotlib.pyplot as plt
import struct
import time

'''
This streamlines the SNAP configuration process.


outline:
1. Imports

2. This description

3. Variables.  Ultimately these will be read from a configuration file.

4. Defines functions

5. Calls functions to configure the snap and packetizer

TODO:
--Maybe make the configuration variables, (including gain/shift ? ) be read from a file.


'''
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
configfile = r'sampleconfig_SNAP_spectrometer.txt'
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
         'SNAPIP',
         'SNAPPORT',
         'DESTMACS',
         'DESTINATION_IP_ADDRESSES',
         'DESTINATION_PORTS',
         'START_CHANNEL']
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
SNAPIP  = paramdict['SNAPIP']     # 32 bit integer, IP address of SNAP
SNAPPORT =paramdict['SNAPPORT']   #integer, port number for ethernet1 to send from
DESTMACS = paramdict['DESTMACS']  #List of 256 48 bit integers, lists all destination MAC addresses for ethernet1.
DESTINATION_IP_ADDRESSES = paramdict['DESTINATION_IP_ADDRESSES'] #list of 32-bit integers, lists destination IP addresses in order of corresponding subbands. 
DESTINATION_PORTS =  paramdict['DESTINATION_PORTS'] #list of integers, lists destination ports in order of corresponding subbands. 
START_CHANNEL = paramdict['START_CHANNEL'] # Lowest channel number of the set of 320 channels to send out the first ethernet port.

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
start = 332 # in order to have it actually start on 330. TODO fix firmware so this offset isn't needed
print "TODO: Fix in firmware the offset which is currently compensated for here."
I = np.ones(reorder_length);

reorder_length = T*Bt*F*M;
I = np.ones(reorder_length)

m_test = np.zeros(reorder_length);
b_test = np.zeros(reorder_length);
f_test = np.zeros(reorder_length);
t_test = np.zeros(reorder_length);
p_test = np.ones(reorder_length);

j=0;
for b in range(B):
    for t in range(T):
        for f in range(F):
            for m in range(M):
                i = Bt*F*M*t + F*b +f + Bt*F*m +start;
                p = m+f+b+t;
                I[2*j] = i;
                I[2*j +1] = 1;
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


