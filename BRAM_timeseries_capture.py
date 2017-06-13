from __future__ import division
import corr
import numpy as np
import matplotlib.pyplot as plt
import struct
import time
from argparse import ArgumentParser

p = ArgumentParser(description = 'Read raw ADC output from BRAM and plot histogram of ADC states.')
p.add_argument('rpi', type = str, default = '', help = 'specify the ip address of the raspberry pi which is connected to the SNAP')
p.add_argument('-i', '--n_integration', dest = 'N_INT', type = int, default = 1, help = 'Number of times to read BRAM for each histogram')
p.add_argument('-m', '--mark', dest = 'MARK', type = str, default = '', help = 'Pyplot plotting mark (e.g."r." to plot red dots)')
p.add_argument('-d', '--duration', dest = 'D', type = int, default = -1, help = 'Number of times to generate a histogram.  -1 continually plots until stopped by ctrl c.')
p.add_argument('-p', '--print', dest = 'FNAME', type = str, default = None, help = 'save rms in a file')

#argument for data selection by whole ADC (for use with the f-engines)
p.add_argument('-a', '--adc', dest = 'ADC', type = int, default = 2, help = 'Choose which ADC to write to BRAM (for use with f-engines only)')

# arguments for data selection by individual stream (for use with flow through mode)
p.add_argument('-sa', '--streamA', dest = 'STREAM0', type = int, default = 8, help = 'For flow through mode: Choose the first antenna data stream to send.')
p.add_argument('-sb', '--streamB', dest = 'STREAM1', type = int, default = 9, help = 'For flow through mode: Choose a second antenna data stream to send.')
p.add_argument('-sc', '--streamC', dest = 'STREAM2', type = int, default = 10, help = 'For flow through mode: Choose a third antenna data stream to send.')
p.add_argument('-sd', '--streamD', dest = 'STREAM3', type = int, default = 11, help = 'For flow through mode: Choose a fourth antenna data stream to send.')

args = p.parse_args()
rpi = args.rpi
ADC = args.ADC
N_INT = args.N_INT
MARK = args.MARK
D = args.D
FNAME = args.FNAME

STREAM0 = args.STREAM0
STREAM1 = args.STREAM1
STREAM2 = args.STREAM2
STREAM3 = args.STREAM3

if D< -1:
	print 'd must be >= -1'
	exit()
# Connect to SNAP.  SNAP should already be configured by running SNAP_config
r = corr.katcp_wrapper.FpgaClient(rpi,7147)
time.sleep(2)
if r.is_connected:
    print 'Connected to SNAP'
else:
    print 'Not connected to SNAP'
    
# define function to grab histogram

# RAW ADC OUTPUT FROM BRAM
def ADC_histogram(adc,n_int,mark):
    #adc is the number of the ADC chip whose output you want to store (choose 0,1 or 2)
    #n_int is the number of times to read the ADC output BRAM
    if 'choose_adc' in r.listdev():
	r.write_int('choose_adc',adc)
    elif 'sel_stream_0' in r.listdev():
        r.write_int('sel_stream_0',STREAM0)
        r.write_int('sel_stream_1',STREAM1)
        r.write_int('sel_stream_2',STREAM2)
        r.write_int('sel_stream_3',STREAM3)
    else:
        print "Could not choose data stream. \n Please check that your SNAP is running firmware that supports reading ADC output from BRAM via this script."
        exit()  
        
    rawstring = r.read('raw_adc_output', 4096)
    integers = np.fromstring(rawstring,'>i1')
    timeseries = np.reshape(integers, (1024,4)) #each column is a different adc output 
    rms = np.zeros(n_int)
    for t in range(n_int):
        rawstring = r.read('raw_adc_output', 4096)
        integers = np.fromstring(rawstring,'>i1')
        new_timeseries = np.reshape(integers, (1024,4)) #each column is a different adc output
        rms[t] = np.std(new_timeseries[:,2]) #TODO make it easier to switch which stream to print stats

        timeseries = np.concatenate((timeseries, new_timeseries), axis = 0)
        time.sleep(1e-3)
    rms_bar = np.mean(rms)
    rms_err = np.std(rms,ddof = 1)
    #print 'rms_bar', rms_bar
    #print 'rms_err', rms_err

    for i in range(4):
        plt.subplot(2,2,i+1)
        plt.title('ADC Output Histogram')
        plt.ylabel('Count')
        plt.xlabel('ADC Output')
        bins = range(-128,129)
        histogram = np.histogram(timeseries[:,i],bins)
        plt.plot(range(-128,128),histogram[0],mark)
        #print 'max=', max(timeseries[:,i]), 'min=',  min(timeseries[:,i])
        #print 'mean = ', np.mean(timeseries[:,i]),
        #print 'sigma =', np.std(timeseries[:,i])
    return rms_bar

# generate output histograms and plot timeseries
n = 0
stats = []
while n < D or D==-1:
#while True:
	#print n #TODO print on one line and erase
	n+=1
	plt.figure(1)
	rms = ADC_histogram(ADC,N_INT,MARK)
        #print rms
        stats.append(rms)
        if FNAME:
		np.savetxt(FNAME,stats) 
	plt.figure(20)
	rawstring = r.read('raw_adc_output', 4096)
	integers = np.fromstring(rawstring,'>i1')
	timeseries = np.reshape(integers, (1024,4)) #each column is a different adc output
	plt.plot(timeseries[:,1],'.')
	#plt.draw()
	#plt.show(block=False)
	#time.sleep(4)
	plt.ion()
	##plt.show() TODO Make plotting optional
	plt.pause(0.5)
	#plt.close('all')
	time.sleep(1)
