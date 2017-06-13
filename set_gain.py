
# script to set fft shift and post-PFB digital gain for SNAP f-engine
# FPGA should already be programmed using SNAP_spectrometer_config.py

import corr
import time
from argparse import ArgumentParser
import sys

#Parse command line arguments
p = ArgumentParser(description = 'python set_gain.py rpi [OPTIONS]')
p.add_argument('rpi', type = str, default = '', help = 'specify the ip address of the raspberry pi which is connected to the SNAP')
p.add_argument('-s', '--shift', dest = 'fft_shift', type = bin, default = 0b0010010010, help = 'Ten bit number to set how often to shift to prevent overflow in the fft. Each bit represents one stage in the fft. Set a bit to one to shift on that stage, zero to not shift.')
p.add_argument('-g', '--gain', dest = 'gain', type = int , default = 2**5, help = 'Digital gain for the post-pfb requantization.')
 
args = p.parse_args()
rpi = args.rpi
shift = args.fft_shift
gain = args.gain

#shift = 0b010001000100 
#gain =2**8

print sys.argv

r = corr.katcp_wrapper.FpgaClient(rpi,7147)
time.sleep(2)
if r.is_connected:
	print 'Connected to SNAP'
	
	shift_was =str(bin(r.read_int('fftshift')))
	print 'fft shift was %s' %shift_was
	print 'setting shift to %s' %str(bin(shift))
	r.write_int('fftshift', shift)

	gain_was = r.read_int('gain')
	print 'post-pfb digital gain was %s' %gain_was
	print 'setting gain to %s' %str(gain)
	r.write_int('gain', gain)

	exit()
else:
	print 'Not connected to SNAP'
	exit()

