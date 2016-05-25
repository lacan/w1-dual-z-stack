# VisiView Macro for Melina Scholze
# Based on initial code by Dr. Arne Seitz, BIOP
# With help from Visitron Systems
# Written by Olivier Burri, BIOP
# Last update: 26 May 2016

import sys
import os
import time   # To assess timings 
import pickle # To save and write data to a file

# ============== Define Classes ============== #
class TicToc:
	""" Manages time measurement in s"""
	t1 = 0
	t2 = 0
	
	def tic(self):
		self.t1 = time.time()
	
	def toc(self):
		self.t2 = time.time()
		delta = round( self.t2 - self.t1 )
		return delta

# Instantiate Timer
T = TicToc()

# ============== Some Aesthetics ============== #

# Input Dialog size
VV.Macro.InputDialog.Top   = 20
VV.Macro.InputDialog.Left  = 100
VV.Macro.InputDialog.Width = 350

# ============ Initialize Variables =========== #
has_crop = False

save_dir           = VV.Acquire.Sequence.Directory

time_interval = 10 #seconds
cycles        = 5 
# Load defaults if present

defaults_path = 'defaults.txt'
if os.path.isfile(defaults_path):
        with open(defaults_path) as f:
            time_interval, cycles = pickle.load(f)

        
# ============== Show Output Window ============== #
VV.Macro.PrintWindow.IsVisible = True


#***************************************************
# ================ Dialog Directory ================
#***************************************************
VV.Macro.InputDialog.Initialize('Define Acquisition Parameters',True)
VV.Macro.InputDialog.AddDirectoryVariable('Save Folder', 'save_dir', save_dir)
VV.Macro.InputDialog.AddFloatVariable('Time Interval [s]', 'time_interval', time_interval, 0, 100000, 1)
VV.Macro.InputDialog.AddFloatVariable('Cycles', 'cycles', cycles, 0, 100000, 1)
VV.Macro.InputDialog.Show()


# File PATHS

region_path        = save_dir+'\\crop-area-camera'
bf_settings_path   = save_dir+"\\biop-macro-bf.acq"
fluo_settings_path = save_dir+"\\biop-macro-fluo.acq"

# Save Settings
with open(defaults_path, 'w') as f:
    pickle.dump([time_interval, cycles], f)


#***************************************************
# =========== Dialog First Stack Plane =============
#***************************************************

# Load settings if already present
try :
	VV.Acquire.Settings.Load(bf_settings_path)
except :
	print sys.exc_value, ': No previous BF settings exist'

# Run Live Mode
VV.Acquire.FullCameraArea()
VV.Acquire.StartLive();

VV.Macro.InputDialog.Initialize('Define your Brightfield Parameters: ',True)
VV.Macro.InputDialog.AddLabelOnly('1. Define a region for CCD Cropping.')
VV.Macro.InputDialog.AddLabelOnly('2. Choose Z Series parameters.')
VV.Macro.InputDialog.AddLabelOnly('And click OK...')

# Display Macro Dialog with instructions
VV.Macro.InputDialog.Show()


# ========== Save Necessary Parameters =========== #

# Live Not selected by default, need to set it manually
VV.Window.Selected.Handle = VV.Window.GetHandle.Live
# Save region if it exists to crop afterwards during acquisition
if  VV.Window.Regions.Count == 1:
	VV.Edit.Regions.Save(region_path)
	has_crop = True

#Stop acquisition
VV.Acquire.Stop()

# Save variables for first stack
z1_focus = VV.Focus.ZPosition
z1_wave  = VV.Acquire.WaveLength.Illumination
z1_exp   = VV.Acquire.ExposureTimeMillisecs

# Save BF Settings
VV.Acquire.Settings.Save(bf_settings_path)



#***************************************************
# =========== Dialog Second Stack Plane ============
#***************************************************

# Load settings if already present
try:
	VV.Acquire.Settings.Load(fluo_settings_path)
except :
	print sys.exc_value, ': No previous Fluo settings exist'

VV.Acquire.StartLive();
VV.Macro.InputDialog.Initialize('Define your Fluorescence Parameters',True)
VV.Macro.InputDialog.AddLabelOnly('1. Choose Illumination(s), exposure, laser, settings')
VV.Macro.InputDialog.AddLabelOnly('2. Choose Z Series parameters')
VV.Macro.InputDialog.AddLabelOnly('And click OK...')

# Display Macro Dialog with instructions
VV.Macro.InputDialog.Show()

# Save Focus, may be useful
z2_focus = VV.Focus.ZPosition
VV.Acquire.Stop()

#Save FLUO Settings
VV.Acquire.Settings.Save(fluo_settings_path)

#***************************************************
# ============== Perform Acquisition ===============
#***************************************************

# Define directory for saving stacks
tmp_dir = save_dir+"\\"+str(int(round(time.time(),0)))+"\\"

# Check that it exists and create it otherwise
d = os.path.dirname(tmp_dir)
if not os.path.exists(d):
	os.makedirs(d)

# Load camera region if it exists
if has_crop:
	VV.Acquire.LoadCameraRegion(region_path)

# Enclose in a try loop, to make sure we can interrupt the
# acquisition as necessary (CTRL-C or ESC)
try:
	for t in range(0,cycles):
		
		# Save memory, close all windows
		VV.Window.CloseAll(False)
		
		# Start timing the acquisition cycle
		T.tic()

	# == Load BF == #

		# Load settings for BF
		VV.Acquire.Settings.Load(bf_settings_path)

		# Load region for cropping camera, if present
		if has_crop:
			VV.Acquire.LoadCameraRegion(region_path)

		# Overwrite the prefix for all brightfield images
		VV.Acquire.Sequence.BaseName = "BF"

		#Overwrite directory for acquisitions
		VV.Acquire.Sequence.Directory = tmp_dir

		# Run BF Acquisition
		VV.Acquire.Sequence.Start()
		VV.Macro.Control.WaitFor('VV.Acquire.IsRunning','!=','true')

		# End of first acquisition
		a1 = T.toc();
		print 'BF took ', str(a1), 's'
		
		# == Load FLUO == #
	# Load settings for FLUO
		VV.Acquire.Settings.Load(fluo_settings_path)

		# Load region for cropping camera, if present
		if has_crop:
			VV.Acquire.LoadCameraRegion(region_path)

		# Overwrite the prefix for all fluorescence images
		VV.Acquire.Sequence.BaseName = "Fluo"

		#Overwrite directory for acquisitions
		VV.Acquire.Sequence.Directory = tmp_dir

		# Run FLUO Acquisition
		VV.Acquire.Sequence.Start()
		VV.Macro.Control.WaitFor('VV.Acquire.IsRunning','!=','true')
		
		# Get end of acquisition cycle
		delta = T.toc()
		print 'FLUO took ', str(delta - a1), 's'
		
		print 'Acquisition #', str(t), ' took ', str(delta), 's'
		cycle_time = time_interval - delta
		
		# Wait until it's time for the next cycle
		if cycle_time > 0:
			print 'waiting ' ,str(cycle_time), ' s before next cycle...'
			time.sleep(cycle_time)
		else:
			print 'Cycle time negative (',cycle_time,'s). Continuing immediately'

# This allows for the keyboard to interrupt the acquision
except KeyboardInterrupt:
	pass


#Reset directory for acquisitions
VV.Acquire.Sequence.Directory = save_dir
print "Finished in "+tmp_dir

