# VisiView Macro for Melina Scholze
# Based on initial code by Dr. Arne Seitz, BIOP
# With help from Visitron Systems
# Written by Olivier Burri, BIOP
# Last update: 04 July 2018
# 	- July 2018: Fixes issue for positioning the dialog.


version = '1.02'
# Protocol
# 1. Launch Macro
# 2. Define Experiment Settings:
#		- Save Directory
#		- Interval between cycles
#		- Number of Cycles
#
# 2. Define BRIGHTFIELD Settings
#		- Exposure Time
#		- Z Series
#	        - Camera Region
#
#    == Before Pressing OK, Make sure that LIVE is still running ==
#	            === Otherwise we cannot get the Region ===
#
#		== All settings will be saved in .acq file in the ==
#		==           previously defined folder            ==
#
# 3. Define Fluorescence Settings
#		- Exposure Time for each wavelengths
#		- Wavelength(s)
#		- Z Series
#
#		== All settings will be saved in .acq file in the ==
#		==           previously defined folder            ==
#
#    === AFTER PRESSING OK, THE ACQUISITON STARTS



# ==== START CODE ==== ##
import sys
import os
import time   # To assess timings
import pickle # To save and write data to a file
import re	  # To manage windows properly

# ============== Define Classes ============== #
class TicToc:
	""" Manages time measurement in ms"""
	t1 = 0
	t2 = 0

	def tic(self):
		self.t1 = int(round(time.time()*1000))

	def toc(self):
		self.t2 = int(round(time.time()*1000))
		delta = self.t2 - self.t1
		return delta


# ==== SAVE AND GET OTHER SETTINGS ====
def saveSettings(path, *args):
	try:
		# Save Settings
		with open(path, 'w') as f:
			pickle.dump(args, f)
	except:
		print 'Could not save values'

def loadSettings(path):
	vars = {}
	try:
		# Save Settings
		with open(path) as f:
			vars = pickle.load(f)
	except:
		print 'Could not load values'

	return vars

# Save settings in text format for use in subsequent macros

def saveSettingsForMacro(path, **info):
        try:
                f = open(path, 'w')
                for name, value in info.items():
                	f.write(name+' : '+str(value)+'\n')
                f.close()
        except:
                print 'Could not save settings to ', path

def killWindows():
	# VisiView Macro
	names = VV.Window.NameList

	# Keep only the ones without the highest number
	r = re.compile('A\d.*-(\d+).*')


	iteration = [int(n.group(1)) for win in names for n in [r.search(win)] if n ]
	if iteration and iteration is not None:
		largest = max((iteration))
	
		to_kill = [ names[i] for i,v in enumerate(iteration) if v < largest ]
	
		if (len(to_kill) > 0):
			for name in to_kill:
				handle = VV.Window.GetHandle.Name(name)
				VV.Window.Selected.Handle = handle
				VV.Window.Selected.Close(False)



# ==== MANAGE LASER POWER ====
# Because Laser power is not saved we manage this on our own

# This variable acts as a 'switch' statement and maps a
# simpler name for the lasers to the actual names needed
# by VV.
global switcher

switcher = {
	'405': 'Toptica405_Laser405',
	'488': 'Toptica488_Laser488',
	'561': 'MMC D/A_Laser561',
	'640': 'Toptica640_Laser640'
	}

# Laser Power Getter, give vavelength as String
def getLaserPower(wavelength):

	value = VV.Illumination.GetComponentSlider(switcher.get(wavelength))
	return value

# Value setter. Value gets set but panel does not update until you open/close it...
def setLaserPower(wavelength, value):

	VV.Illumination.SetComponentSlider(switcher.get(wavelength), value)
	# Check that the power was set
	new_value = VV.Illumination.GetComponentSlider(switcher.get(wavelength))
	# Reload Panel, to see updated values...


# Convenience, get all laser powers
def getAllLaserPowers():
	i405 = getLaserPower('405')
	i488 = getLaserPower('488')
	i561 = getLaserPower('561')
	i640 = getLaserPower('640')
	return { '405': i405, '488': i488, '561': i561,  '640':i640 }
	
# Convenience, set all laser powers
def setAllLaserPowers(laser_powers):
	for laser in laser_powers:
		setLaserPower(laser, laser_powers[laser])
	
	VV.Panel.Dialog.Close()
	VV.Macro.Control.Delay(0.5,'sec')
	VV.Panel.Dialog.Show()

# Runs a given acquisition
def runAcquisition(dir, acquisition_name, settings_path, has_crop, region_path, z_focus):
	# Load settings for BF
	VV.Acquire.Settings.Load(settings_path)	
	VV.Acquire.Settings.Load(settings_path)
	# Load region for cropping camera, if present

	if has_crop:
		VV.Acquire.LoadCameraRegion(region_path)

	# Overwrite the prefix for all images
	VV.Acquire.Sequence.BaseName = acquisition_name

	#Overwrite directory for acquisitions
	VV.Acquire.Sequence.Directory = dir
	VV.Focus.ZPosition = z_focus
	
	# Run Acquisition
	VV.Acquire.Sequence.Start()
	VV.Macro.Control.WaitFor('VV.Acquire.IsRunning','!=','true')



# ============== Show Output Window ============== #
VV.Macro.PrintWindow.IsVisible = True

# Instantiate Timer
T = TicToc()


# ============ Initialize Variables =========== #

has_crop = False

save_dir      = VV.Acquire.Sequence.Directory

prefix        = ''
time_interval = 10 #seconds
cycles        = 5
a1_z_focus    = 175
a2_z_focus    = 175

a1_name   	  = 'A1'
a2_name   	  = 'A2'


lasers        = { '405': 10, '488': 10, '561': 10,  '640': 10 }


# ==== START ==== #
print 'Welcome to the double acquisition macro v'+version


# ====== IF Settings exist ====== #
if os.path.isfile(save_dir+'\\expt-settings.txt'):
	lasers, a1_z_focus, a2_z_focus, time_interval, cycles, prefix = loadSettings(save_dir+'\\expt-settings.txt')

print lasers
setAllLaserPowers(lasers)

saveSettingsForMacro(save_dir+'\\settings.txt', a1_z_focus=a1_z_focus)

#***************************************************
# ================ Dialog Directory ================
#***************************************************
VV.Macro.InputDialog.Initialize('Define Acquisition Parameters',True)
VV.Macro.InputDialog.AddDirectoryVariable('Save Folder', 'save_dir', save_dir)
VV.Macro.InputDialog.AddStringVariable('Acquisition Prefix', 'prefix', prefix)
VV.Macro.InputDialog.AddFloatVariable('Time Interval [s]', 'time_interval', time_interval, 0, 100000, 1)
VV.Macro.InputDialog.AddFloatVariable('Cycles', 'cycles', cycles, 0, 100000, 1)
# ============== Some Aesthetics ============== #
VV.Macro.InputDialog.Top   = 20
VV.Macro.InputDialog.Left  = 100
VV.Macro.InputDialog.Width = 350

VV.Macro.InputDialog.Show()


# File PATHS
region_path        = save_dir+'\\crop-area-camera'
a1_settings_path   = save_dir+'\\biop-macro-a1.acq'
a2_settings_path   = save_dir+'\\biop-macro-a2.acq'
expt_settings_path = save_dir+'\\expt-settings.txt'


#***************************************************
# =========== Dialog First Stack Plane =============
#***************************************************

# Load settings if already present
try :
	VV.Acquire.Settings.Load(a1_settings_path)
	VV.Acquire.Settings.Load(a1_settings_path)
except :
	print sys.exc_value, ': No previous '+a1_name+' settings exist'

# Run Live Mode
VV.Acquire.FullCameraArea()
VV.Acquire.StartLive()

# Set focus from previous settings
VV.Focus.ZPosition = a1_z_focus

VV.Macro.InputDialog.Initialize('Define your '+a1_name+' Parameters: ',True)
VV.Macro.InputDialog.AddLabelOnly('1. Define a region for CCD Cropping.')
VV.Macro.InputDialog.AddLabelOnly('2. Choose Z series parameters.')
VV.Macro.InputDialog.AddLabelOnly('And click OK...')

# Display Macro Dialog with instructions
VV.Macro.InputDialog.Show()

# ========== Save Necessary Parameters =========== #

# Live Not selected by default, need to set it manually
live_handle = VV.Window.GetHandle.Live
VV.Window.Selected.Handle = live_handle

# Make sure Live is on when looking at the available Regions
if not live_handle.IsEmpty:
	# Save region if it exists to crop afterwards during acquisition
	if  VV.Window.Regions.Count == 1:
		VV.Edit.Regions.Save(region_path)
		has_crop = True



# Save variables for first stack
a1_z_focus = VV.Focus.ZPosition

# Save Pixel Size, for macro in ImageJ
px_size     = VV.Image.Calibration.Value

#Stop acquisition
VV.Acquire.Stop()

# Save BF Settings
VV.Acquire.Settings.Save(a1_settings_path)



#***************************************************
# =========== Dialog Second Stack Plane ============
#***************************************************

# Load settings if already present
try:
	VV.Acquire.Settings.Load(a2_settings_path)
	VV.Acquire.Settings.Load(a2_settings_path)
except :
	print sys.exc_value, ': No previous '+a2_name+' settings exist'


# Get focus
a2_z_focus = VV.Focus.ZPosition

# Show Acquisition
VV.Acquire.StartLive();

VV.Macro.InputDialog.Initialize('Define your Fluorescence Parameters',True)
VV.Macro.InputDialog.AddLabelOnly('1. Choose Illumination(s), exposure, laser, settings')
VV.Macro.InputDialog.AddLabelOnly('2. Choose Z series parameters')
VV.Macro.InputDialog.AddLabelOnly('And click OK...')

# Display Macro Dialog with instructions
VV.Macro.InputDialog.Show()

# Save Focus, may be useful
a2_z_focus = VV.Focus.ZPosition
VV.Acquire.Stop()

#Save FLUO Settings
VV.Acquire.Settings.Save(a2_settings_path)

# Get and Save Laser Powers
lasers = getAllLaserPowers()

# Save Experiment Settings
saveSettings(expt_settings_path, lasers, a1_z_focus, a2_z_focus, time_interval, cycles, prefix)


#***************************************************
# ============== Perform Acquisition ===============
#***************************************************

# Closing windows with delay to make sure Melina can see the last stacks
a1_windows = []
a2_windows = []


# Define directory for saving stacks
tmp_dir = save_dir+"\\"+str(int(round(time.time(),0)))+"\\"

# Check that it exists and create it otherwise
d = os.path.dirname(tmp_dir)
if not os.path.exists(d):
	os.makedirs(d)

# Save settings in a format that our macros can read!
saveSettingsForMacro(tmp_dir+"\\Settings.txt", lasers=lasers, a1_z_focus=a1_z_focus, a2_z_focus=a2_z_focus, time_interval=time_interval, cycles=cycles, prefix=prefix, px_size=px_size)

# Enclose in a try loop, to make sure we can interrupt the
# acquisition as necessary (CTRL-C or ESC)
# Add cycle counter in case of script stop
n_cycles = 1
try:
	for t in range(0,cycles):

		# Save memory, close all windows
		# VV.Window.CloseAll(False) # Stop using it

		# Start timing the acquisition cycle
		T.tic()


	# == Load A1 == #
		runAcquisition(tmp_dir, a1_name+'-'+prefix+'-', a1_settings_path, has_crop, region_path, a1_z_focus)

		# Get name of current window and append to list
		a1_windows.append(VV.Window.GetHandle.Active)#SOMETHING)

		# End of A1 acquisition
		a1 = T.toc();
		print a1_name, ' took ', str(a1), 'ms'
		

	# == Load A2 == #
		runAcquisition(tmp_dir, a2_name+'-'+prefix+'-', a2_settings_path, has_crop, region_path, a2_z_focus)

		# Get name of current window and append to list
		a2_windows.append(VV.Window.GetHandle.Active)
		
		
		# End of A2 acquisition
		delta = T.toc()
		print a2_name, ' took ', str(delta - a1), 'ms'


	# == End of Acquisition Cycle == #
		print 'Acquisition #', str(n_cycles), ' took ', str(delta), 'ms'
		cycle_time = time_interval*1000 - delta

		# Wait until it's time for the next cycle
		if cycle_time > 0:
			print 'waiting ' ,str(cycle_time), ' ms before next cycle...'
			time.sleep(cycle_time/1000)
		else:
			print 'Cycle time negative (',cycle_time,'ms). Continuing immediately'

		# == Close the last windows if there are already 3 open
		# Close all older windows
		killWindows()
		
		#Increment cycle number
		n_cycles = n_cycles+1

# This allows for the keyboard to interrupt the acquision
except KeyboardInterrupt:
	pass
	# Resave the settings, to keep in mind the right number of cycles
	saveSettingsForMacro(tmp_dir+"\\Settings.txt", lasers=lasers, a1_z_focus=a1_z_focus, a2_z_focus=a2_z_focus, time_interval=time_interval, cycles=n_cycles, prefix=prefix, px_size=px_size)


#Reset directory for acquisitions
VV.Acquire.Sequence.Directory = save_dir
print "Finished in "+tmp_dir
