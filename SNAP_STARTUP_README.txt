
BRAM_timeseries_capture.py
	- reads ADC output from BRAM and plots histogram.

SNAP_spectrometer_config_with_pps.py
	- configures spectrometer, including programming boffile. Starts data flow at the end of configuration; synchronisation to pps happens with a different script. This is for a boffile which includes pps input, but packetization is synchronised from software if no pps is plugged in. Ethernet reset no longer involves writing software registers.  Ethernet reset, including the necessary valid_down occurs automatically when a sync pulse is issued, no matter whether the sync is forced from software or triggered on a pps pulse.

sync_start.py
	- synchronise to 1pps for time stamped data capture

set_gain1.py
set_gain.py
	Either of the set_gain scripts should be run after the configuration script in order to set the post-pfb gain and the fft shift. TODO: pick which one works better and fix it, rather than having two that sort of work.

SNAP_spectrometer_config_with_pps_old.py
	-Same as above config script but ethernet reset is managed by writing to software registers.

SNAP_spectrometer_config_old.py
	-Same as above but has no pps capability.
