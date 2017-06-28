# UTMOST-SNAP

This repository has code for configuring and controlling a few different pieces of firmware to use on the SNAP board(s) at Molonglo Observatory. This README file assumes the reader is a Molonglo observer, or is a SNAP board user looking for an example configuring an f-engine spectrometer with ethernet packetiser. My python code depends on the library corr (CASPER library which includes a python wrapper around KATCP telnet commands to communicate with the SNAP).  The rest of this document outlines how to use the SNAP configuration code.  For a quick list of instructions, skip to the last section.

My firmware at Molonglo is already stored on the Raspberry Pi connected to the SNAP. When the SNAP board is powered on, the FPGA firmware needs to be programmed with one of the available boffiles. When firmware is loaded onto the SNAP, any software registers in the firmware initially hold the value zero.  The configuration code in this repository handles loading the firmware, setting appropriate values to registers, and starting up the ethernet packetiser.

## Programming and Configuring the FPGA

You have three choices of configuration script, depending on the firmware you want, and all of them take an argument which is the name of a file of configuration parameters.  

1. SNAP_spectrometer_config_with_pps.py 

Run this code to set up an f-engine for a frequency range that matches UTMOST2D. This firmware requires that the SNAP is connected to the observatory pulse-per-second (PPS) signal, 197MHz sample clock, and one SFP+ ethernet link.


2. UTMOST2D_SNAP_config.py

Run this code to set up the UTMOST2D f-engine, which uses both SFP+ ethernet ports and sends twice as many frequency channels as the UTMOST version does.  The SNAP should be connected to observatory PPS and 194.12MHz sample clock.


3. flowthrough_config.py

Instead of an f-engine, this is the firmware for flowthrough mode, which sends raw ADC output for any four of the twelve RF inputs. The SNAP board should be connected to one SFP+ link, observatory PPS, and sample clock at the desired frequency.

An example parameter file for each of the three is included in the repository, with comments in the file explaining what each of the parameters do. Edit these to change, for example, the IP addresses or the frequency channels to send.

All of the configuration scripts finish by telling you to calibrate the ADCs, which expects that you'll use the standard SNAP ADC calibration software (written by Zuhra Abdurashidova). I use ADC gain = 4.

The f-engine configuration code doesn't set the fft-shift or the digital gain for the requantisation, because it's convenient to keep that step separate, for ease of re-adjusting.  Do this with set_gain.py. 

  Usage:
  
  python set_gain.py rpi -g \<gain\> -s \<shift\>
  
  The required argument rpi is the IP address of the raspberry pi connected to the SNAP. The other arguments control requantisation     gain and fft shift,  respectively, and if not specified these will be set to a reasonable default. Running python set_gain.py -h will give help information.  

(Digression: The fft shift is a ten bit integer in which each bit corresponds to one of the stages in the fft. If the bit is set to one, a bit shift will happen on that stage of the fft.  Some shifts are necessary to prevent overflow, but too many effectively cause a loss in dynamic range.  I've set a default which works well. If you want to decrease the number of shifts, watch out for overflows in the fft.) 

## Starting the Ethernet Packetiser
For a time-stamped observation, the ethernet packetiser needs to send data that corresponds to the boundary of a PPS pulse. This is accomplished using sync_start.py, which takes the SNAP IP address as an argument and sends the start timestamp to the computer that is receiving the ethernet packets (e.g. bf08).  Running sync_start.py will only succeed if the destination computer is running voltage capture software with a socket open, awaiting this timestamp.

Other than a time-stamped voltage capture, it's useful to have the SNAP to sending packets of f-engine output to use for level-setting, bandpass monitoring, etc.  All my firmware that uses pps also has the ability to force a start or reset of the packetiser on a signal from software at any time.  The configuration code SNAP_spectrometer_config_with_pps.py, UTMOST2D_SNAP_config.py, and flowthrough_config.py all automatically start the packetiser.  This part will work even if a PPS signal is not connected.

## A couple other useful tools:

diagnostics.py

If the SNAP has been configured and yet no data packets from the SNAP are arriving, this is a good first test to run.  It reads various registers on the SNAP to check the packet rate, the status of the ethernet links, and the pps input, and outputs the results in fairly self-explanatory messages.  If no problems are found, then from the SNAP board’s point of view the packetiser and the ethernet links are functioning. Note that this does not check where the packets are being sent and whether they are being received. If the SFP+ is connected in a loop back to itself, diagnostics.py should report that everything is working, even though the packets are going nowhere. 

If diagnostics.py finds nothing wrong and packets still aren't appearing, the next tests to try are verifying (by looking at the configuration file) that the SNAP was configured with the intended addresses and ports and then running a packet tool such as Wireshark on the destination machine.

BRAM_timeseries_capture.py

This reads raw ADC output from BRAM in blocks of 1024 timesamples. It plots a timeseries of one of the data streams and histograms for four data streams.  This is useful for checking the ADC levels when adjusting the power of the input RF signal. When used with f-engine firmware, all four data streams from any one ADC chip are written to BRAM. When used with flow through mode, any four data streams can be selected. Options are explained in the help text.

## Quick Instructions for F-engine Start-up, e.g. after a power outage:

1. Make sure it's powered on and that RF input, ethernet output, PPS input, and sample clock input are all connected.

2. Configure the FPGA. For example, run:

python UTMOST2D_SNAP_config.py sampleconfig_UTMOST2D.txt

3. Set the gain:
python set_gain.py \< IP address of rpi \>

4. Calibrate the ADC.



