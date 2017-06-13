import corr
import numpy as np
import matplotlib.pyplot as plt
import struct
import time

PI_IP = '10.66.146.30' #string, IP of host raspberry pi

#BOFFILE  = 'adc_to_gbe_pps_2017-3-29_2355.bof'
BOFFILE = 'adc_to_gbe_pps_2017-4-3_2316.bof'

SNAPID = 0xff #8 bit integer, identifies this particular snap board
SNAPMAC = 0x02020a000002 #48 bit integers, MAC for SNAP
SNAPIP  = 0x0a000002     # 32 bit integer, IP address of SNAP
SNAPPORT = 50000   #integer, port number to send from
DESTMACS = [0x0060DD46BFD9 for i in range(256)] #List of 256 48 bit integers, lists all possible destination MAC addresses
DEST_IP = 0x0a000003 #32 bit integer, destination IP
DEST_PORT = 50000 #destination port

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

# Connect to SNAP
r = connect_to_snap(PI_IP)

# load boffile
progfpga(BOFFILE)

#configure ethernet
configurethernet()

#send software start
resetandsync()

print "Now run 'python ~/adc16/adc16_init.py %s  -s -d 1 -g <adcgain>'" %(PI_IP + ' ' + BOFFILE)
