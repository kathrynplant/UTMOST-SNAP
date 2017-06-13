import corr
import time
'''This script runs a few tests checking the software registers that confirm whether the ethernet packetizer and pps are working.  Before running this script, the SNAP should be configured with either firmware that uses pps and ethernet (i.e. a recent spectrometer or flowthrough mode). This is designed to be a first diagnostic to use before trying to capture the UDP packets. '''

r = corr.katcp_wrapper.FpgaClient('10.66.146.30',7147)

time.sleep(2)
if r.is_connected():
    print 'Connected to SNAP.'
else:
    print 'Not connected to SNAP.'
    exit()

try:
    r.read_int('ethernet_status')
    r.read_int('pps_count')
    r.read_int('eof_counter')

except RuntimeError:
    print "Please check that the SNAP is programmed with the intended boffile, because the relevant software registers could not be read."
    exit()

print "Checking ethernet link"
status = r.read_int('ethernet_status')
if status&4:
    print "From the SNAP point of view, the ethernet link is up. Good."
else:
    print "Ethernet link is down. Not good."
if status&2: 
    print "Ethernet buffer is almost full. Not good."
if status&1:
    print "Ethernet buffer has overflowed. Not good."

print "Making a rough estimate of the pps input and packet rate. Wait a while please."
print "The packet rate should be estimated to within a few thousand packets. The test should also count 15 pps pulses, plus or minus one."
c1 = r.read_int('pps_count')
p1 = r.read_int('eof_counter')
time.sleep(15)
p2 = r.read_int('eof_counter')
c2 = r.read_int('pps_count')

print "PPS count should be 15 by now, and " ,(c2 - c1), "pulses have been counted."
print "The measured packet rate (by counting end of frame pulses) is ", (p2 - p1)/15., "packets per second."
print "All done testing!"

if (c2 - c1) == 0:
    print "Check that pps is connected, because no pulses have been detected in 15 seconds."

if (p2 - p1) == 0:
   print "No end of frame pulses pulses have been counted. Check that a sync pulse has been sent to start the packetizer."


