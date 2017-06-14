import corr
import time
'''This script runs a few tests checking the software registers that confirm whether the ethernet packetizer and pps are working.  Before running this script, the SNAP should be configured with firmware that uses pps and ethernet (i.e. a recent spectrometer or flowthrough mode). This is designed to be a first diagnostic to use before trying to capture the UDP packets. '''

#----------------------- Connect to the SNAP ---------------------------
r = corr.katcp_wrapper.FpgaClient('10.66.146.30',7147)

time.sleep(2)
if r.is_connected():
    print 'Connected to SNAP.'
else:
    print 'Not connected to SNAP.'
    exit()
#----------- Determine whether the SNAP is running firmware that uses one SFP+ or two ------------------

#try:
#    r.read_int('ethernet_status')
#    r.read_int('pps_count')
#    r.read_int('eof_counter')

#except RuntimeError:
#    Yprint "Please check that the SNAP is programmed with the intended boffile, because the relevant software registers could not be read."
#    exit()

listdev = r.listdev()
eof_counters = []
ethernet_blocks = []
if ('eof_counter' in listdev):
    print "The firmware currently loaded uses one SFP+ ethernet port."
    eof_counters.append('eof_counter')
    ethernet_blocks.append('ethernet_status')

if 'eof1_counter' and 'eof2_counter' in listdev:
    print "The firmware currently loaded uses both SFP+ ethernet ports."
    eof_counters.append('eof1_counter')
    eof_counters.append('eof2_counter')
    ethernet_blocks.append('ethernet1_status')
    ethernet_blocks.append('ethernet2_status')

try:
    for string in (eof_counters + ethernet_blocks + ['pps_count']):
        r.read_int(string)
except RuntimeError:    
    print "Please check that the SNAP is programmed with the intended boffile, because some of the relevant software registers could not be read."
    exit()


print ' \n'

#------------------------- Check Ethernet Link(s) ----------------------------------------------
print "Checking status of ethernet link(s):"
for block in ethernet_blocks:
    name = block[:-7]
    status = r.read_int(block)
    if status&4:
    	print "From the SNAP point of view, the ", name, " link is up. Good."
    else:
        print name, " link is down. Not good."
    if status&2: 
        print name, " buffer is almost full. Not good."
    if status&1:
        print name, " buffer has overflowed. Not good."

print '\n'
#------------------------ estimate packet rate -----------------------------------
print "Making a rough measurement of the packet rate, by reading the end-of-frame counter, waiting 10 seconds, and then reading again. The packet rate should be estimated to within a few thousand packets (that error is from the time to read registers; a larger error may be a problem)." 
p1 =[]
p2 =[]
for e in eof_counters:
    p1.append(r.read_int(e))
time.sleep(10.) 
for e in eof_counters:
    p2.append( r.read_int(e))

if len(eof_counters) == 1:
    if (p2 - p1) == 0:
        print "No end of frame pulses pulses have been counted. Check that a sync pulse has been sent to start the packetizer."
    print "The measured packet rate (by counting end of frame pulses) is ", (p2[i] - p1[i])/10., "packets per second."

if len(eof_counters) ==2:
    for i in range(2):
        if (p2[i] - p1[i]) == 0:
            print "No end of frame pulses pulses have been counted for ethernet block ", i, " . Check that a sync pulse has been sent to start the packetizer."
        print "For ethernet block ", i,", the measured packet rate (by counting end of frame pulses) is ", (p2[i] - p1[i])/10., "packets per second."

print '\n'
#------------------------ check pps ---------------------------------------------------
print "Checking pps. Wait to count 10 pps pulses."
c1 = r.read_int('pps_count')
time.sleep(10)
c2 = r.read_int('pps_count')
if (c2 - c1) == 0:
    print "Check that pps is connected, because no pulses have been detected in 10 seconds."
print "PPS count should be 10 by now, and " ,(c2 - c1), "pulses have been counted."
print "All done testing!"
