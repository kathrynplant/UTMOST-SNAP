import corr
import numpy as np
import matplotlib.pyplot as plt
import struct
import time

#------------------- Set configuration parameters --------------------

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
configfile = r'sampleconfig_flowthrough.txt'
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
         'DEST_IP',
         'DEST_PORT']

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
DEST_IP = paramdict['DEST_IP'] #list of 32-bit integers, lists destination IP addresses in order of corresponding subbands. The first 10 are for ethernet1, the last 10 for ethernet2.
DEST_PORT =  paramdict['DEST_PORT'] #list of integers, lists destination ports in order of corresponding subbands. The first 10 are for ethernet 1, the last 10 are for ethernet 2.



#----------------------- Define relevant functions ---------------------
def connect_to_snap(piip):
    # connect to snap
    r = corr.katcp_wrapper.FpgaClient(piip,7147)
    time.sleep(2)
    if r.is_connected():
        print 'Connected to SNAP'
    else:
        print 'Not connected to SNAP'
	exit()
    return r
        
def progfpga(name_of_bof):
    #load the bof
    if name_of_bof in r.listbof():
        print 'Found the boffile, now programming the FPGA.'
        print r.progdev(name_of_bof), 'done'
    else:
        print 'The raspberry pi does not have that boffile.'
        

def configurethernet():
    # configure ethernet
    print 'Configuring the 10Gb ethernet'
    r.config_10gbe_core('ten_Gbe_v2',SNAPMAC,SNAPIP,SNAPPORT,DESTMACS,gateway = 0)
    print 'Configuring destination IP address and port'
    r.write_int('tx_dest_ip', DEST_IP)
    r.write_int('tx_dest_port', DEST_PORT)
    print 'ethernet is ready to go.'

def resetandsync():
    #reset ethernet block and send sync pulse
    print 'Sending pulse to reset ethernet and sync.'
    r.write_int('force_new_sync',1)
    time.sleep(0.1)
    r.write_int('force_new_sync',0)
    print 'Done. Ethernet status = %d', r.read_int('ethernet_status')
    return

#--------------------- main --------------------------------
# Connect to SNAP
r = connect_to_snap(PI_IP)

# load boffile
progfpga(BOFFILE)

#configure ethernet
configurethernet()

#send software start
resetandsync()

print "Now run Zuhra's adc calibration. Run: \n 'python ~/adc16/adc16_init.py %s  -s -d 1 -g <adcgain>'" %(PI_IP + ' ' + BOFFILE)
