/* 
 * Action Bar description file : Open Images Acquired with Multi-Acquisition Python Script for Visitron W1
 * Olivier dot Burri at epfl dot ch
 * Created on: June 2nd 2016 for Melina Scholze, Goenczy Lab
 * 
 * DESCRIPTION:
 * The W1 Python script saves a text file called "Settings.txt" inside each acquisition folder
 * This files contains just enough information to reconstruct the not-so easy to work with format
 * output by VisiView.
 * 
 * We want to load all single channel timepoints into a stack and merge all channels that have the right number of Z
 * 
 */


/*
 * Running the ActionBar
 */
sep = File.separator;
// Install the BIOP Library

call("BIOP_LibInstaller.installLibrary", "BIOP"+sep+"BIOPLib.ijm");

run("Action Bar","/plugins/ActionBar/W1_Read_Stacks.ijm");

exit();

<codeLibrary>

/* 
 *  Necessary for the Settings Text File, setData, getData
 */
function toolName() {
	return "W1 Stacks";
}

/*
 * Borrowed from BIOPLib, opens a file and allows it to be read by the getData functions, without the prompt
 */
function loadFile(file) {
	//Get the contents 
	filestr = File.openAsString(file); 
	lines = split(filestr, "\n"); 
	 
	//Open the file and parse the data 
	settingName = getWinTitle();
	 
	t = "["+settingName+"]"; 
	 
	// If something is already open, keep it as-is. 
	if(!isOpen(settingName)) { 
		run("New... ", "name="+t+" type=Table"); 
	} 
	selectWindow(settingName); 
	for (i=0; i<lines.length; i++) { 
		print(t, "\\Update"+i+":"+lines[i]); 
	} 
}

/* This function does everything
 *  Opens the settings file, loads what is needed
 *  Uses Import Sequence to load all the STK files for a given time series
 *  Then combines the channels for timeseries with more than 1 channel
 */
function openFolder() {
	sep = File.separator;

	// Image directory
	dir = getDirectory("Acquisition Folder");
	setBatchMode(false);
	// Get the acquisition file
	if (File.exists(dir+sep+"Settings.txt")) {
		loadFile(dir+sep+"Settings.txt");

		// Load useful info: 
		//  - cycles is the number of timepoints
		//  - prefix is the name of the experiment
		
		cycles = parseInt(getData("cycles"));
		prefix = getData("prefix");
		px_size = getData("px_size");
		
		// Now perform the import of A1 and A2. The macro so far only allows for two acquisitions
		// Though this part of the code handles any number...
		
		// If File ends in .stk
		files = getFileList(dir);
		files = Array.sort(files);
		loadedIds = "";
		for( i=0; i<files.length; i++) {
			if (endsWith(files[i], ".stk")) {
				currentAcq = substring(files[i], 0,2);
				currentChan= substring(files[i], lastIndexOf(files[i], "_")+1, lastIndexOf(files[i], ".") );
				id = currentAcq+currentChan;
				print(wasNotLoaded(id, loadedIds));
				if(wasNotLoaded(id, loadedIds)) {
					loadedIds+=","+id;
					fileId = dir+sep+files[i];
					print(wasNotLoaded(id, loadedIds), fileId, id);
					//run("Bio-Formats Importer", "open=["+fileId+"] group_files view=Hyperstack stack_order=XYCZT contains="+currentChan);
					run("Image Sequence...", "open=["+fileId+"] file="+currentChan+" sort");
					
					nZ = nSlices / cycles;
					run("Stack to Hyperstack...", "order=xyczt(default) channels=1 slices="+nZ+" frames="+cycles+" display=Color");
					// Keep Z Step but change px size
					getVoxelSize(vx,vy,vz,U);
					setVoxelSize(px_size,px_size,vz,U);
					
					wait(100);
					rename(currentAcq+"-"+prefix+"-"+currentChan);
					//waitForUser;
				}
			}
		}

		
		// Now check what to merge in terms of channels
		// This part only handles two Acquisitions (A-files)
		openImages = getList("image.titles");

		mergeAcquisition("A1");
		setBatchMode("show");

		mergeAcquisition("A2");
		setBatchMode("show");

	
	setBatchMode(false);
	run("Synchronize Windows");
}

function mergeAcquisition(startText) {
	openImages = getList("image.titles");
	iF = newArray(0);
	lab = newArray(0);
	for(i=0; i<openImages.length; i++) {
		if (startsWith(openImages[i], startText)) {
			iF = Array.concat(iF, openImages[i]);
			selectImage(openImages[i]);
			lab = Array.concat(lab,getInfo("slice.label"));
		}
	}
		
	if (iF.length >1) {
		str = "c1=["+iF[0]+"]";

		for(i=1; i<iF.length; i++) {
			str+= " c"+(i+1)+"=["+iF[i]+"]";
		}
		
		run("Merge Channels...", str+" create");
		selectImage("Merged");

		// Fix the labels
		getDimensions(nx,ny,nc,nz,nt);
		for(c=0;c<nc;c++) {
			for(z=0;z<nz;z++) {
				for(t=0;t<nt;t++) {
					Stack.setPosition(c+1, z+1, t+1) ;
					setMetadata("Label", lab[c]);
				}
			}
		}
			
		
		
		
		
	} else {
		selectImage(iF[0]);
	}
	rename(startText+"-"+prefix);
}
	
function wasNotLoaded(current, olds) {
	others = split(olds,",");
	for (i=0; i<others.length; i++) {

		if (others[i] == current)
			return false;
	}
	return true;
}
</codeLibrary>

//********* Select Image
<line>
<button>
label=Load W1 Stack
arg=<macro>
	openFolder();
</macro>
</line>

<line>
//******* Close all images except current one
<button>
label=Close All but Current
arg=<macro>
	close("\\Others");
</macro>
</line>