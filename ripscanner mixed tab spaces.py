#Import packages

import tkinter as tk
from tkinter import messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np

#*********************************************************#
#*********************** SETTINGS ************************#

numPeaksPerFrame = 10; #No. oscillations to fit on the scope screen when aquiring data
numDivHoriz = 12; #No. horiz. divs on scope screen
numDivVert = 8; #No. vert divs on scope scren
vertExpandFactor = 1.5; #factor by which to expand the vertical scale when guessing how to scale vertically (bigger # shrinks signal more, 1 is min)

#*********************************************************#
#*********************************************************#

#Declare sample buffers
freqs = []; #Sample frequencies
ampls = []; #Sample amplitudes

#Define data arrays
lxi = []; #Low-max in
lxo = []; #Low-max out
lxf = []; #Low-max freqs
lx3 = []; #Low-max CH3
lx4 = []; #Low-max CH4
lni = []; #Low-min in
lno = []; #Low-min out
lnf = []; #Low-min freqs
ln3 = []; #Low-min CH3
ln4 = []; #Low-min CH4

mxi = []; #Mid-max in
mxo = []; #Mid-max out
mxf = []; #Mid-max freqs
mx3 = []; #Mid-max CH3
mx4 = []; #Mid-max CH4
mni = []; #Mid-min in
mno = []; #Mid-min out
mnf = []; #Mid-min freqs
mn3 = []; #Mid-min CH3
mn4 = []; #Mid-min CH4

hxi = []; #High-max in
hxo = []; #High-max out
hxf = []; #High-max freqs
hx3 = []; #High-max CH3
hx4 = []; #High-max CH4
hni = []; #High-min in
hno = []; #High-min out
hnf = []; #High-min freqs
hn3 = []; #High-min CH3
hn4 = []; #High-min CH4

basei = []; #Baseline in
baseo = []; #baseline out
basef = []; #Baseline freqs
base3 = []; #Baseline CH3
base4 = []; #baseline CH4

fmeas =[]; #Freq. buffer
omeas = []; #output ampl. buffer
imeas = []; #Input ampl. buffer
meas3 = []; #CH3 buffer
meas4 = []; #CH4 buffer

print("General Purpose Transfer Function Scanner");
print("\n**** Copyright 2019, Giesbreceht Electronics ****");

#Define Subroutines
##def measVsAmp(fmeas, omeas, imeas, meas3, meas4):
##    fmeas[:] = [12, 50, 100, 330, 1e3, 3.3e3, 20e3];
##    omeas[:] = [1.9, 2.3, 7, 19, 40, 20, 2.4];
##    imeas[:] = [2, 2, 2, 2, 2, 2, 2];
##    pass;


#
# Initializes the test equipment and sets them up to
# scan or generate the appropriate signals.
#
def initializeTestEquipment():
	rm = visa.ResourceManager()
	# Get the USB device, e.g. 'USB0::0x1AB1::0x0588::DS1ED141904883'
	instruments = rm.list_resources()
	scope_addr = list(filter(lambda x: 'DS1Z' in x, instruments))
	awg_addr = list(filter(lambda x: 'SDG2X' in x, instruments))
	if len(scope_addr) != 1 or len(awg_addr) != 1:
		print('Bad instrument list', instruments)
		sys.exit(-1)
	scope = rm.open_resource(scope_addr[0], timeout=30, chunk_size=1024) # bigger timeout for long mem
	print("Connected to scope");
	awg = rm.open_resource(awg_addr[0], timeout=30, chunk_size=1024) # bigger timeout for long mem
	print("Connected to generator");

	#Initialize oscilloscope to collect data
	#scope.write("MEAS:COUN:SOUR CHAN1");
	scope.write("MEAS:STAT:ITEM FREQ,CHAN1");
	#scope.write("MEAS:STAT:ITEM VRMS,CHAN1");
	#scope.write("MEAS:STAT:ITEM VRMS,CHAN2");
	scope.write("MEAS:STAT:ITEM VPP,CHAN1");
	scope.write("MEAS:STAT:ITEM VPP,CHAN2");
	scope.write("MEAS:STAT:ITEM VAVG,CHAN3");
	scope.write("MEAS:STAT:ITEM VAVG,CHAN4");

#
# Collect a single data point using frequency as the independent variable.
#
#
def collectFreq():
	freqs.append(float(scope.query("MEAS:COUN:VAL?")));
	added = 0;
	try:
		freqs.append(float(scope.query("MEAS:STAT:ITEM? CURR,FREQ,CHAN1")));
		added = 1;
		in_vpp.append(float(scope.query("MEAS:STAT:ITEM? CURR,VPP,CHAN1")));
		added = 2;
		#		in_rms.append(float(scope.query("MEAS:STAT:ITEM? CURR,VRMS,CHAN1")));
		added = 3;
		out_vpp.append(float(scope.query("MEAS:STAT:ITEM? CURR,VPP,CHAN2")));
		added = 4;
		#		out_rms.append(float(scope.query("MEAS:STAT:ITEM? CURR,VRMS,CHAN2")));
		added = 5;
		level_avg.append(float(scope.query("MEAS:STAT:ITEM? CURR,VAVG,CHAN3")));
		added = 6;
		i = len(freqs)-1;
		#			print("\t** f = " + "{:09.4e}".format(freqs[i]) + " Hz\t**\tVin = " + "{:09.4e}".format(in_vpp[i]) + " Vpp\t" + "{:09.4e}".format(in_rms[i]) + " Vrms\t**\tVout = " + "{:09.4e}".format(out_vpp[i]) + " Vpp\t" + "{:09.4e}".format(out_rms[i]) + "Vrms\t**\tVlevel = " + "{:09.4e}".format(level_avg[i]) + "V");
		print("\t** f = " + "{:09.4e}".format(freqs[i]) + " Hz\t**\tVin = " + "{:09.4e}".format(in_vpp[i]) + " Vpp\t**\tVout = " + "{:09.4e}".format(out_vpp[i]) + " Vpp\t**\tVlevel = " + "{:09.4e}".format(level_avg[i]) + "V");
		saved = False;
		noncorrupted_length = noncorrupted_length + 1;
	except:
		
		while (len(freqs) > noncorrupted_length):
			del freqs[noncorrupted_length];
		
		while (len(in_vpp) > noncorrupted_length):
			del in_vpp[noncorrupted_length];
		
		while (len(in_rms) > noncorrupted_length):
			del in_rms[noncorrupted_length];
		
		while (len(out_vpp) > noncorrupted_length):
			del out_vpp[noncorrupted_length];
		
		while (len(out_rms) > noncorrupted_length):
			del out_rms[noncorrupted_length];
		
		while (len(level_avg) > noncorrupted_length):
			del level_avg[noncorrupted_length];
		
		print("\a\tMeasurement error (" + str(added) + "). Point not recorded.");
		while (True):
			ri = raw_input("\t\tEnter 'z' to continue: ");
			if (ri == "z" or ri == "Z"):
				break;

#
# Collect a single data point using input-amplitude as the independent variable
#
#
def collectAmpl():
	pass;

#
# Print the collected data
#
def printTable():
	print("-----------------------------------------------------------------------------------------");
	print("|                                   Data Collected                                      |");
	print("-----------------------------------------------------------------------------------------");
	print("|Freq (Hz)\t\t|In (Vpp)\t\t|Out (Vpp)\t\t|Out (V_lvl)\t|");
	print("-----------------------------------------------------------------------------------------");
	for i in range(len(freqs)):
		print("|"+ "{:09.4e}".format(freqs[i]) + "\t\t|" + "{:09.4e}".format(in_vpp[i]) + "\t\t|" + "{:09.4e}".format(out_vpp[i]) + "\t\t|" + "{:09.4e}".format(level_avg[i]) + "\t|");
		print("-----------------------------------------------------------------------------------------");

def resetAutoNext(win):
    bandEntryScaleRB3.select();
    win.destroy();

def executeAutoNext():
    if(gain.get() == 2): #Baseline (set ot low-min)
        bandEntryBandRB1.select(); #Low
        bandEntryScaleRB2.select(); #min
    elif (gain.get() == 0 and band.get() == 0): #Low-min (set to low-max)
        bandEntryScaleRB1.select(); #max
    elif(gain.get() == 1 and band.get() == 0): #low-max (set to mid-min)
        bandEntryBandRB2.select(); #Mid
        bandEntryScaleRB2.select(); #min
    elif(gain.get() == 0 and band.get() == 1): #Mid-min (set to mid-max)
        bandEntryScaleRB1.select(); #max
    elif(gain.get() == 1 and band.get() == 1): #Mid-max (set to High-min)
        bandEntryBandRB3.select(); #High
        bandEntryScaleRB2.select(); #min
    elif(gain.get() == 0 and band.get() == 2): #High-min (set to High-max)
        bandEntryScaleRB1.select(); #max
    elif(gain.get() == 1 and band.get() == 2): #High-max (Give message)
        win = tk.Toplevel()
        win.title("Auto-Next Complete");
        tk.Label(win, image=imgAutoNext).grid(row=0, column=0, rowspan=3);
        tk.Label(win, text="Scanned High-Band at max-gain. Select", font='FONT_LARGE').grid(row=0, column=1, columnspan=2, sticky='W');
        tk.Label(win, text="a different band or gain, or select ", font='FONT_LARGE').grid(row=1, column=1, columnspan=2, sticky='W');
        tk.Label(win, text="'Reset' for auto-next to engage again.", font='FONT_LARGE').grid(row=2, column=1, columnspan=2, sticky='W');
        tk.Button(win, text="Okay", command=win.destroy).grid(row=3, column=1);
        tk.Button(win, text="Reset", command=lambda: resetAutoNext(win)).grid(row = 3, column=2);
##        tk.messagebox.showinfo("Auto-Next Complete", "Scanned High-band at max-gain. Select a different band for auto-next to engage again.");

#
# Measre a transfer function (using 1+ data points).
#
#
def meas(fmeas, omeas, imeas, meas3, meas4):

    firstPoint = True;

    amplitude = 1;

    for idx in len(freqs):
        #Set frequency
		#DO: Set AWG to frequency =

        #Set amplitude

        #Configure scope settings
        if (aquisitionMode.get() == 0): #Automatic

            #Determine time/div setting
            totalTime = 1/freqs[p]*numPeaksPerFrame;
            timePerDiv = totalTime/numDivHoriz;
            #DO: Load timePerDiv

            #Determine volts/div setting
            if (firstPoint): #guess it's about the size of the input if no idea
                voltsPerDiv = amplitude/numDivVert*vertExpandFactor;
            while ("" == "WAVE DOESN'T FIT ON SCREEN"): #DO: Impliiment this check!!
                #Triple vertical size
                pass;
            if ("" == "WAVE IS SUPER TINY"): #DO: Impliment this check!!
                #get Vpp -> set resolution to vertExpandFactor*Vpp
                pass;
            if ("" == "HAVING TROUBLE TRIGGERING"):
                #Set to sinlge trigger

                #Adjust trigger level to avg

                #Force trigger if no luck...
                pass;
        else: #From file
            print("Aquisition settings from file not yet suppored.");
            return False;
            

        #Read input amplitude (CH1)

        #DO: Get CH1 VPP

        #Read input frequency (CH1)

        #DO: get CH1 freq

        #Read output amplitude (CH2)

        #DO: get CH2 VPP

        #Read CH3

        #DO: get CH3

        #Read CH4

        #DO: get CH4
    
    return True;


#
# Processes everything for a scan. Reads info from the GUI, files, etc. and
# begins a scan (using the meas() function, which in turn, makes multiple calls
# to collectFreq() or collectAmpl()).
#
def scan():

    #Get sample frequencies/amplitudes
    if not getSampleFreqsAmpls():
        tk.messagebox.showerror("Scan Failed!", "Failed to determine sample frequencies/amplitudes");
        return False;

    #Clear buffers
    fmeas =[];
    omeas = [];
    imeas = [];
    meas3 = [];
    meas4 = [];

    #Perform measurements
    if (not meas(fmeas, omeas, imeas, meas3, meas4)):
        tk.messagebox.showerror("Scan Failed!", "Failed to complete measurements.");
##    if (scanMode.get() == 0): #Amplitudes
##        if (not measVsAmp(fmeas, omeas, imeas, meas3, meas4)):
##            tk.messagebox.showerror("Scan Failed!", "Failed to complete measurements.");
##    elif(scanMode.get() == 1 or scanMode.get() == 2): #Freqs.
##        measVsFreq(fmeas, omeas, imeas, meas3, meas4);

#    print("fmeas: " + str(fmeas))

	print("Scan completed successfully.");

    #Add to graph
    gains = np.multiply(20, np.log10(np.divide(omeas, imeas))).tolist();
    plot.semilogx(fmeas, gains);
##    plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [1, 13, 14, 26, 16, 12, 1.5], color='green', marker='o', linestyle='dashed', linewidth=1, markersize=3);
##    plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [1, 0, 1.6, 2, 2.5, 16, 22]);

    #Get band & gain & update status panels
	if (scanMode.get() == 2): #Only if multiband update status panels
		if band.get() == 0:
			bandstr = "Low";
			if gain.get() == 0:
				gainstr = "Min";
				lowMinBandScanImg.configure(image=imgScanned);
			elif gain.get() == 1:
				gainstr = "Max";
				lowMaxBandScanImg.configure(image=imgScanned);
			elif gain.get() == 2:
				gainstr = "Flat";
				baseBandScanImg.configure(image=imgScanned);
			else:
				gainstr = "ERROR ("+str(gain)+")";
		elif band.get() == 1:
			bandstr = "Mid";
			if gain.get() == 0:
				gainstr = "Min";
				midMinBandScanImg.configure(image=imgScanned);
			elif gain.get() == 1:
				gainstr = "Max";
				midMaxBandScanImg.configure(image=imgScanned);
			elif gain.get() == 2:
				gainstr = "Flat";
				baseBandScanImg.configure(image=imgScanned);
			else:
				gainstr = "ERROR ("+str(gain)+")";
		elif band.get() == 2:
			bandstr = "High";
			if gain.get() == 0:
				gainstr = "Min";
				highMinBandScanImg.configure(image=imgScanned);
			elif gain.get() == 1:
				gainstr = "Max";
				highMaxBandScanImg.configure(image=imgScanned);
			elif gain.get() == 2:
				gainstr = "Flat";
				baseBandScanImg.configure(image=imgScanned);
			else:
				gainstr = "ERROR ("+str(gain)+")";
		else:
			bandstr = "ERROR ("+str(band)+")";

		print("Scaned band: "+bandstr + "\tGain: " + gainstr);

    redrawGraph();

    #Auto-next band
    if (autonext.get() == 1 and scanMode.get() == 2): #If auto-next is enabled and the scan mode is "freqs (mult-band)"
        executeAutoNext();

#
# Reads the GUI to determine the sample frequencies or amplitudes
#
def getSampleFreqsAmpls():
    global freqs, ampls;

	if (scanMode.get() == 1 or scanMode.get() == 2): #Frequency is indep-var
        if scale.get() == 0: #Linear
            try:
                a = (float(scaleNumberEntry0.get()));
            except:
                print("Failed to read start frequency ("+scaleNumberEntry0.get()+")");
                return False;
            try:
                b = (float(scaleNumberEntry2.get()));
            except:
                print("Failed to read end frequency ("+scaleNumberEntry2.get()+")");
                return False;
            try:
                c = int(scaleNumberEntry1.get());
            except:
                print("Failed to read number of frequency steps ("+scaleNumberEntry1.get()+")");
                return False;
            freqs = np.linspace(a, b, c)
        elif scale.get() == 1: #Log
            try:
                a = np.log10(float(scaleNumberEntry0.get()));
            except:
                print("Failed to read start frequency ("+scaleNumberEntry0.get()+")");
                return False;
            try:
                b = np.log10(float(scaleNumberEntry2.get()));
            except:
                print("Failed to read end frequency ("+scaleNumberEntry2.get()+")");
                return False;
            try:
                c = int(scaleNumberEntry1.get());
            except:
                print("Failed to read number of frequency steps ("+scaleNumberEntry1.get()+")");
                return False;
            freqs = np.logspace(a, b, c)
            print(a, b, c);
        elif scale.get() == 2: #From File
            print("Note: Frequencies from file are not yet supported.");
            return False;
        elif scale.get() == 3: #From entry
            try:
                freqstr = scaleListEntry.get().split(",");
                freqs = [];
                for fs in freqstr:
                    freqs.append(float(fs));
            except:
                print("Failed to read frequency entries");
                return False;

        fstr = "";
        for f in freqs:
            fstr = fstr+ str(round(f)) + " ";
        print("Frequencies: " + fstr)
		
		ampls = [];
		
	else: #Amplitude is indep-var
		freqs=[]; #Clear the frequencies - this tells the program it is in amplitude mode
        if scale.get() == 0: #Linear
            try:
                a = (float(scaleNumberEntry0.get()));
            except:
                print("Failed to read start amplitude ("+scaleNumberEntry0.get()+")");
                return False;
            try:
                b = (float(scaleNumberEntry2.get()));
            except:
                print("Failed to read end amplitude ("+scaleNumberEntry2.get()+")");
                return False;
            try:
                c = int(scaleNumberEntry1.get());
            except:
                print("Failed to read number of amplitude steps ("+scaleNumberEntry1.get()+")");
                return False;
            ampls = np.linspace(a, b, c)
        elif scale.get() == 1: #Log
            try:
                a = np.log10(float(scaleNumberEntry0.get()));
            except:
                print("Failed to read start amplitude ("+scaleNumberEntry0.get()+")");
                return False;
            try:
                b = np.log10(float(scaleNumberEntry2.get()));
            except:
                print("Failed to read end amplitude ("+scaleNumberEntry2.get()+")");
                return False;
            try:
                c = int(scaleNumberEntry1.get());
            except:
                print("Failed to read number of amplitude steps ("+scaleNumberEntry1.get()+")");
                return False;
            ampls = np.logspace(a, b, c)
        elif scale.get() == 2: #From File
            print("Note: Frequencies from file are not yet supported.");
            return False;
        elif scale.get() == 3: #From entry
            try:
                amplstr = scaleListEntry.get().split(",");
                ampls = [];
                for fs in amplstr:
                    ampls.append(float(fs));
            except:
                print("Failed to read frequency entries");
                return False;

        fstr = "";
        for f in ampls:
            fstr = fstr+ str(round(f)) + " ";
        print("Amplitudes: " + fstr)
        
    return True

def save():
    print("Saving not yet supported");

#
# Prints a help file to the terminal
#
def help():
    with open("helpfile.txt", 'r') as fin:
        print(fin.read())

##def scaleNumberDecrement():
##    try:
##        nv=int(scaleNumberEntry.get())-1;
##        scaleNumberEntry.delete(0,tk.END)
##        scaleNumberEntry.insert(0,str(nv))
##    except:
##        print("Failed to read value ("+scaleNumberEntry.get()+")");
##        print(type(scaleNumberEntry.get()));
##        pass;
##
##def scaleNumberIncrement():
##    try:
##        nv=int(scaleNumberEntry.get())+1;
##        scaleNumberEntry.delete(0,tk.END)
##        scaleNumberEntry.insert(0,str(nv))
##    except:
##        print("Failed to read value ("+scaleNumberEntry.get()+")");
##        print(type(scaleNumberEntry.get()));
##        pass;

# Updates the graph pane
def redrawGraph():
    print("redrawing graph");
    global plot, canvas;
##    plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [25, 18, 14, 6, 2, 1, .1]);
##    plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [1, 13, 14, 26, 16, 12, 1.5], color='green', marker='o', linestyle='dashed', linewidth=1, markersize=3);
##    ##plot.cla();
##    plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [1, 0, 1.6, 2, 2.5, 16, 22]);
    plot.set_ylim(-40, 40);
    plot.set_xlim(10, 25e3);
    plot.set_xlabel("Frequency (Hz)");
    plot.set_ylabel("Gain (dB)");
    plot.set_title("Transfer Function");
    plot.grid(b=True);
    canvas.draw()

def setScan0():
    disableMultibands();
    setToAmplMode();

def setScan1():
    disableMultibands();
    setToFreqMode();

def setScan2():
    enableMultibands();
    setToFreqMode();

def disableMultibands():
    bandEntryBandRB1.configure(state = tk.DISABLED)
    bandEntryBandRB2.configure(state = tk.DISABLED)
    bandEntryBandRB3.configure(state = tk.DISABLED)

    bandEntryScaleRB1.configure(state = tk.DISABLED)
    bandEntryScaleRB2.configure(state = tk.DISABLED)
    bandEntryScaleRB3.configure(state = tk.DISABLED)

    bandEntryAutoProgress.configure(state = tk.DISABLED)

    lowMaxBandScanLabel.configure(fg='#999999');
    lowMinBandScanLabel.configure(fg='#999999');
    midMaxBandScanLabel.configure(fg='#999999');
    midMinBandScanLabel.configure(fg='#999999');
    highMaxBandScanLabel.configure(fg='#999999');
    highMinBandScanLabel.configure(fg='#999999');
    baseBandScanLabel.configure(fg='#999999');

    pass;

def setToFreqMode():
    scaleNumberLabel0.configure(text='Start (Hz):');
    scaleNumberLabel2.configure(text='End (Hz):');

def setToAmplMode():
    scaleNumberLabel0.configure(text='Start (Vpp):');
    scaleNumberLabel2.configure(text='End (Vpp):');
    
def enableMultibands():
    bandEntryBandRB1.configure(state = tk.NORMAL)
    bandEntryBandRB2.configure(state = tk.NORMAL)
    bandEntryBandRB3.configure(state = tk.NORMAL)

    bandEntryScaleRB1.configure(state = tk.NORMAL)
    bandEntryScaleRB2.configure(state = tk.NORMAL)
    bandEntryScaleRB3.configure(state = tk.NORMAL)

    bandEntryAutoProgress.configure(state = tk.NORMAL);

    lowMaxBandScanLabel.configure(fg='blue');
    lowMinBandScanLabel.configure(fg='blue');
    midMaxBandScanLabel.configure(fg='blue');
    midMinBandScanLabel.configure(fg='blue');
    highMaxBandScanLabel.configure(fg='blue');
    highMinBandScanLabel.configure(fg='blue');
    baseBandScanLabel.configure(fg='blue');

    
    pass;

def clearAllBands():

    #Verify action
    if( not tk.messagebox.askokcancel("Data Loss Warning", "This action will delete all unsaved data. Do you want to proceed?")):
        return;

    #Erase data
    lxi = []; #Low-max in
    lxo = []; #Low-max out
    lxf = []; #Low-max freqs
    lx3 = []; #Low-max CH3
    lx4 = []; #Low-max CH4
    lni = []; #Low-min in
    lno = []; #Low-min out
    lnf = []; #Low-min freqs
    ln3 = []; #Low-min CH3
    ln4 = []; #Low-min CH4
    mxi = []; #Mid-max in
    mxo = []; #Mid-max out
    mxf = []; #Mid-max freqs
    mx3 = []; #Mid-max CH3
    mx4 = []; #Mid-max CH4
    mni = []; #Mid-min in
    mno = []; #Mid-min out
    mnf = []; #Mid-min freqs
    mn3 = []; #Mid-min CH3
    mn4 = []; #Mid-min CH4
    hxi = []; #High-max in
    hxo = []; #High-max out
    hxf = []; #High-max freqs
    hx3 = []; #High-max CH3
    hx4 = []; #High-max CH4
    hni = []; #High-min in
    hno = []; #High-min out
    hnf = []; #High-min freqs
    hn3 = []; #High-min CH3
    hn4 = []; #High-min CH4
    basei = []; #Baseline in
    baseo = []; #baseline out
    basef = []; #Baseline freqs
    base3 = []; #Baseline CH3
    base4 = []; #baseline CH4

    #Clear indicators
    lowMaxBandScanImg.configure(image=imgNotscanned);
    lowMinBandScanImg.configure(image=imgNotscanned);
    midMaxBandScanImg.configure(image=imgNotscanned);
    midMinBandScanImg.configure(image=imgNotscanned);
    highMaxBandScanImg.configure(image=imgNotscanned);
    highMinBandScanImg.configure(image=imgNotscanned);
    baseBandScanImg.configure(image=imgNotscanned);

    #Clear graph
    plot.cla();
    redrawGraph();

def ch3sel():
    if (ch3on.get() == 1):
        scanCH3Menu.configure(state=tk.NORMAL);
    else:
        scanCH3Menu.configure(state=tk.DISABLED);

def ch4sel():
    if (ch4on.get() == 1):
        scanCH4Menu.configure(state=tk.NORMAL);
    else:
        scanCH4Menu.configure(state=tk.DISABLED);

#Create GUI

numcols = 3;
numrows = 8;

ctrl=tk.Tk();

imgScanned = tk.PhotoImage(file='scanned.gif');
imgNotscanned = tk.PhotoImage(file='notscanned.gif');
imgAutoNext = tk.PhotoImage(file='autonext82.gif');
##imgAutoNext24 = tk.PhotoImage(file='autonextfull24.gif');

##********** Title
ctrl.title("Rip Scanner");

##********** Row 0
##scanLabel=tk.Label(ctrl, text='Transfer Function Scanner', font='LARGE_FONT');
##scanLabel.grid(row=0, column=0, columnspan=numcols);

modeFrame = tk.Frame(ctrl, relief=tk.RAISED, bd=1);
modeLabel = tk.Label(modeFrame, text="Scanner:", font='LARGE_FONT');
modeLabel.grid(row=0, column=0, columnspan=4);

scanModeLabel = tk.Label(modeFrame, text="Scanned Param.:");
scanModeLabel.grid(row=1, column=0, sticky='E');

scanMode = tk.IntVar();
scanModeRB1 = tk.Radiobutton(modeFrame, text="Amplitude", variable=scanMode, value=0, command=setScan0);
scanModeRB1.grid(row=1, column=1);
scanModeRB2 = tk.Radiobutton(modeFrame, text="Freq.", variable=scanMode, value=1, command=setScan1);
scanModeRB2.grid(row=1, column=2, stick='W');
scanModeRB3 = tk.Radiobutton(modeFrame, text="Freq. (multi-band)", variable=scanMode, value=2, command=setScan2);
scanModeRB3.grid(row=1, column=3, stick='W');

ch3on = tk.IntVar();
ch4on = tk.IntVar();
scanCHxLabel = tk.Label(modeFrame, text="Aux. Channels:");
scanCHxLabel.grid(row=2, column=0, sticky='E');
scanCH3CB = tk.Checkbutton(modeFrame, text="CH3", variable=ch3on, onvalue=1, offvalue=0, command=ch3sel);
scanCH3CB.grid(row=2, column=1, columnspan=1);
scanCH4CB = tk.Checkbutton(modeFrame, text="CH4", variable=ch4on, onvalue=1, offvalue=0, command=ch4sel);
scanCH4CB.grid(row=2, column=3, columnspan=1);

ch3Mode = tk.StringVar()
ch4Mode = tk.StringVar()
ch3Mode.set("Vpp");
ch4Mode.set("Vpp");
scanCHxLabel = tk.Label(modeFrame, text="Aux Measurement:");
scanCHxLabel.grid(row=3, column=0, sticky='E');
scanCH3Menu = tk.OptionMenu(modeFrame, ch3Mode, "Vpp", "Vavg");
scanCH3Menu.grid(row=3, column=1);
scanCH3Menu.configure(width=4);
scanCH3Menu.configure(state=tk.DISABLED);
scanCH4Menu = tk.OptionMenu(modeFrame, ch4Mode, "Vpp", "Vavg");
scanCH4Menu.grid(row=3, column=3);
scanCH4Menu.configure(width=4);
scanCH4Menu.configure(state=tk.DISABLED);

modeFrame.grid(row=0, column=0, columnspan=2);

graphFrame = tk.Frame(ctrl);
##graphLabel = tk.Label(graphFrame, text="Transfer Function", font='LARGE_FONT');
##graphLabel.pack(side=tk.TOP, fil=tk.BOTH, expand=1);
graph = Figure(figsize=(6.5,5.5), dpi=100);
plot = graph.add_subplot(111);
##plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [25, 18, 14, 6, 2, 1, .1]);
##plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [1, 13, 14, 26, 16, 12, 1.5], color='green', marker='o', linestyle='dashed', linewidth=1, markersize=3);
####plot.cla();
##plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [1, 0, 1.6, 2, 2.5, 16, 22]);
##plot.set_ylim(-40, 40);
##plot.set_xlim(10, 25e3);
##plot.grid();
##plot.set_xlabel("Frequency (Hz)");
##plot.set_ylabel("Gain (dB)");
##plot.set_title("Transfer Function");

canvas = FigureCanvasTkAgg(graph, master=graphFrame);
canvas.draw();
canvas.get_tk_widget().pack(side=tk.TOP, fil=tk.BOTH, expand=1);

toolbar=NavigationToolbar2Tk(canvas, graphFrame);
toolbar.update();
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1);

graphFrame.grid(row=0, column=2, rowspan=6);

##canvas.show()

##canvas._tkcanvas.grid(row=1, column=0);

##********** Row 1

aquisitionFrame = tk.Frame(ctrl, relief=tk.RAISED, bd=1);
aquisitionLabel = tk.Label(aquisitionFrame, text="Aquisition:", font='LARGE_FONT');
aquisitionLabel.grid(row=0, column=0, columnspan=3);

aquisitionModeLabel = tk.Label(aquisitionFrame, text="Control Mode:");
aquisitionModeLabel.grid(row=1, column=0, sticky='E');

aquisitionMode = tk.IntVar();
aquisitionModeRB1 = tk.Radiobutton(aquisitionFrame, text="Auto", variable=aquisitionMode, value=0);
aquisitionModeRB1.grid(row=1, column=1);
aquisitionModeRB2 = tk.Radiobutton(aquisitionFrame, text="From File", variable=aquisitionMode, value=1);
aquisitionModeRB2.grid(row=1, column=2, sticky='W');
aquisitionModeLabel = tk.Label(aquisitionFrame, text="File:");
aquisitionModeLabel.grid(row=2, column=0, sticky='E');
aquisitionModeFile = tk.Entry(aquisitionFrame);
aquisitionModeFile.grid(row=2, column=1, columnspan=2);

aquisitionFrame.grid(row=1, column=0, columnspan=2);

##bandEntryLabel=tk.Label(ctrl, text="Band (H,M,L): ");
##bandEntryLabel.grid(row=1, column=0, sticky='E');
##bandEntry=tk.Entry(ctrl);
##bandEntry.grid(row=1, column=1, sticky='W');

##********* Row 2

genFrame = tk.Frame(ctrl, bd=1, relief=tk.RAISED);



genNumberFrame = tk.Frame(genFrame, relief='sunken');
genNumberLabel0 = tk.Label(genNumberFrame, text="Start:");
genNumberLabel0.grid(row=0, column=0);
genNumberLabel1 = tk.Label(genNumberFrame, text="No. Steps:");
genNumberLabel1.grid(row=0, column=1);
genNumberLabel2 = tk.Label(genNumberFrame, text="End:");
genNumberLabel2.grid(row=0, column=2);
##genNumberDec = tk.Button(genNumberFrame, text="Decr.", command=genNumberDecrement);
##genNumberDec.grid(row=1, column=0);
genNumberEntry0 = tk.Entry(genNumberFrame, width=10);
genNumberEntry0.grid(row=1, column=0);
genNumberEntry1 = tk.Entry(genNumberFrame, width=10);
genNumberEntry1.grid(row=1, column=1);
genNumberEntry2 = tk.Entry(genNumberFrame, width=10);
genNumberEntry2.grid(row=1, column=2);
##genNumberIncr = tk.Button(genNumberFrame, text="Incr.", command=genNumberIncrement);
##genNumberIncr.grid(row=1, column=2);
genNumberFrame.grid(row=1, column=1, rowspan=2, columnspan=2);

genFileLabel = tk.Label(genFrame, text="File: ");
genFileLabel.grid(row=3, column=1, sticky='E');
genFileEntry = tk.Entry(genFrame);
genFileEntry.grid(row=3, column=2, sticky='W');

genListLabel = tk.Label(genFrame, text="    Values: ");
genListLabel.grid(row=4, column=1, sticky='E');
genListEntry = tk.Entry(genFrame);
genListEntry.grid(row=4, column=2, sticky='W');

## |||||||||||||||||||||||||||||||||||||||||||||||||||

genFrame = tk.Frame(ctrl, bd=1, relief=tk.RAISED);

genFrameLabel = tk.Label(genFrame, text="Generator:", font='LARGE_FONT');
genFrameLabel.grid(row=0, column=0, columnspan=3);

genAmplMode=tk.IntVar();
genRBLabel = tk.Label(genFrame, text="Ampl.:");
genRBLabel.grid(row=1, column=0);
genRB1 = tk.Radiobutton(genFrame, text="Auto", variable=genAmplMode, value=0);
genRB1.grid(row=2, column=0, sticky='W')
genRB2 = tk.Radiobutton(genFrame, text="File", variable=genAmplMode, value=1);
genRB2.grid(row=3, column=0, sticky='W')


genNumberFrame = tk.Frame(genFrame, relief='sunken');
##genNumberLabel0 = tk.Label(genNumberFrame, text="Freq (Hz):");
##genNumberLabel0.grid(row=0, column=0);
genNumberLabel1 = tk.Label(genNumberFrame, text="Min ampl. (Vpp):");
genNumberLabel1.grid(row=0, column=0);
genNumberLabel2 = tk.Label(genNumberFrame, text="Max ampl. (Vpp):");
genNumberLabel2.grid(row=0, column=1);
##genNumberDec = tk.Button(genNumberFrame, text="Decr.", command=genNumberDecrement);
##genNumberDec.grid(row=1, column=0);
genNumberEntry0 = tk.Entry(genNumberFrame, width=13);
genNumberEntry0.grid(row=1, column=0);
genNumberEntry1 = tk.Entry(genNumberFrame, width=13);
genNumberEntry1.grid(row=1, column=1);
##genNumberEntry2 = tk.Entry(genNumberFrame, width=10);
##genNumberEntry2.grid(row=1, column=2);
##genNumberIncr = tk.Button(genNumberFrame, text="Incr.", command=genNumberIncrement);
##genNumberIncr.grid(row=1, column=2);
genNumberFrame.grid(row=1, column=1, rowspan=2, columnspan=2);

genFileLabel = tk.Label(genFrame, text="Ampl. file: ");
genFileLabel.grid(row=3, column=1, sticky='E');
genFileEntry = tk.Entry(genFrame, width=18);
genFileEntry.grid(row=3, column=2, sticky='W');

genListLabel = tk.Label(genFrame, text="Freq. (Hz): ");
genListLabel.grid(row=4, column=1, sticky='E');
genListEntry = tk.Entry(genFrame, width=13);
genListEntry.grid(row=4, column=2, sticky='W');

##dfltFreqLabel = tk.Label(genFrame, text="Dflt Frequency: ");
##dfltFreqLabel.grid(row=1, column=0);
##dfltFreqEntry = tk.Entry(genFrame, width=10);
##dfltFreqEntry.grid(row=1, column=1);
##
##minAmplLabel = tk.Label(genFrame, text="Min Ampl. (Vpp): ");
##minAmplLabel.grid(row=2, column=0, sticky='E');
##minAmplEntry = tk.Entry(genFrame, width=10);
##minAmplEntry.grid(row=2, column=1, sticky='W');
##
##maxAmplLabel = tk.Label(genFrame, text="Max Ampl. (Vpp): ");
##maxAmplLabel.grid(row=2, column=2, sticky='E');
##maxAmplEntry = tk.Entry(genFrame, width=10);
##maxAmplEntry.grid(row=2, column=3, sticky='W');
##
##fileAmplLabel = tk.Label(genFrame, text="File: ");
##fileAmplLabel.grid(row=3, column=2, sticky='E');
##fileAmplEntry = tk.Entry(genFrame, width=20);
##fileAmplEntry.grid(row=3, column=3, sticky='W');

genFrame.grid(row=2, column=0, columnspan=2);

##********** Row 3

scaleFrame = tk.Frame(ctrl, bd=1, relief=tk.RAISED);

scaleFrameLabel = tk.Label(scaleFrame, text="Sample Points:", font='LARGE_FONT');
scaleFrameLabel.grid(row=0, column=0, columnspan=3);

scale=tk.IntVar();
scaleRB1 = tk.Radiobutton(scaleFrame, text="Linear", variable=scale, value=0);
scaleRB1.grid(row=1, column=0, sticky='W')
scaleRB2 = tk.Radiobutton(scaleFrame, text="Log", variable=scale, value=1);
scaleRB2.grid(row=2, column=0, sticky='W')
scaleRB3 = tk.Radiobutton(scaleFrame, text="From file", variable=scale, value=2);
scaleRB3.grid(row=3, column=0, sticky='W')
scaleRB4 = tk.Radiobutton(scaleFrame, text="From list", variable=scale, value=3);
scaleRB4.grid(row=4, column=0, sticky='W')

scaleNumberFrame = tk.Frame(scaleFrame, relief='sunken');
scaleNumberLabel0 = tk.Label(scaleNumberFrame, text="Start:");
scaleNumberLabel0.grid(row=0, column=0);
scaleNumberLabel1 = tk.Label(scaleNumberFrame, text="No. Steps:");
scaleNumberLabel1.grid(row=0, column=1);
scaleNumberLabel2 = tk.Label(scaleNumberFrame, text="End:");
scaleNumberLabel2.grid(row=0, column=2);
##scaleNumberDec = tk.Button(scaleNumberFrame, text="Decr.", command=scaleNumberDecrement);
##scaleNumberDec.grid(row=1, column=0);
scaleNumberEntry0 = tk.Entry(scaleNumberFrame, width=10);
scaleNumberEntry0.grid(row=1, column=0);
scaleNumberEntry1 = tk.Entry(scaleNumberFrame, width=10);
scaleNumberEntry1.grid(row=1, column=1);
scaleNumberEntry2 = tk.Entry(scaleNumberFrame, width=10);
scaleNumberEntry2.grid(row=1, column=2);
##scaleNumberIncr = tk.Button(scaleNumberFrame, text="Incr.", command=scaleNumberIncrement);
##scaleNumberIncr.grid(row=1, column=2);
scaleNumberFrame.grid(row=1, column=1, rowspan=2, columnspan=2);

scaleFileLabel = tk.Label(scaleFrame, text="File: ");
scaleFileLabel.grid(row=3, column=1, sticky='E');
scaleFileEntry = tk.Entry(scaleFrame);
scaleFileEntry.grid(row=3, column=2, sticky='W');

scaleListLabel = tk.Label(scaleFrame, text="    Values: ");
scaleListLabel.grid(row=4, column=1, sticky='E');
scaleListEntry = tk.Entry(scaleFrame);
scaleListEntry.grid(row=4, column=2, sticky='W');

scaleFrame.grid(row=3, column=0, columnspan=2);

##********** Row 4

bandFrame = tk.Frame(ctrl, relief=tk.RAISED, bd=1);

bandLabel = tk.Label(bandFrame, text="Frequency Band:", font='LARGE_FONT');
bandLabel.grid(row=0, column=0, columnspan=4);

band=tk.IntVar();
bandEntryLabel=tk.Label(bandFrame, text="Band: ");
bandEntryLabel.grid(row=1, column=0);
bandEntryBandRB1 = tk.Radiobutton(bandFrame, text="Low", variable=band, value=0);
bandEntryBandRB1.grid(row=1, column=1)
bandEntryBandRB2 = tk.Radiobutton(bandFrame, text="Mid", variable=band, value=1);
bandEntryBandRB2.grid(row=1, column=2)
bandEntryBandRB3 = tk.Radiobutton(bandFrame, text="High", variable=band, value=2);
bandEntryBandRB3.grid(row=1, column=3)

gain=tk.IntVar();
bandEntryScaleLabel = tk.Label(bandFrame, text="Gain: ");
bandEntryScaleLabel.grid(row=2, column=0);
bandEntryScaleRB1 = tk.Radiobutton(bandFrame, text="Max", variable=gain, value=1);
bandEntryScaleRB1.grid(row=2, column=2)
bandEntryScaleRB2 = tk.Radiobutton(bandFrame, text="Min", variable=gain, value=0);
bandEntryScaleRB2.grid(row=2, column=1)
bandEntryScaleRB3 = tk.Radiobutton(bandFrame, text="All Flat", variable=gain, value=2);
bandEntryScaleRB3.grid(row=2, column=3)

bandEntrySpacerLabel = tk.Label(bandFrame, text="");
bandEntrySpacerLabel.grid(row=3, column=0);

autonext=tk.IntVar();
bandEntryAutoProgress = tk.Checkbutton(bandFrame, text="Auto-next", variable=autonext, onvalue=1, offvalue=0);
bandEntryAutoProgress.grid(row=4, column=1, columnspan=2);
##bandEntryAutoProgressImg = tk.Label(bandFrame, image=imgAutoNext24);
##bandEntryAutoProgressImg.grid(row=4, column=3, columnspan=1, sticky='W');

bandFrame.grid(row=4, column=0, columnspan=2);

##********** Row 5

scanStatusFrame = tk.Frame(ctrl, relief=tk.RAISED, bd=1);
scanstatusLabel = tk.Label(scanStatusFrame, text="Scan Status:", font='LARGE_FONT');
scanstatusLabel.grid(row=0, column=0, columnspan=6);

#Low Band Label
lowBandScanLabel = tk.Label(scanStatusFrame, text="Low Band:   ", fg='black');
lowBandScanLabel.grid(row=1, column=0, sticky='W', columnspan=2);
#Low band status
lowMaxBandScanImg = tk.Label(scanStatusFrame, image=imgNotscanned);
lowMaxBandScanImg.grid(row=2, column=0, sticky='E');
lowMaxBandScanLabel = tk.Label(scanStatusFrame, text="Low Max", fg='blue');
lowMaxBandScanLabel.grid(row=2, column=1, sticky='W');
lowMinBandScanImg = tk.Label(scanStatusFrame, image=imgNotscanned);
lowMinBandScanImg.grid(row=3, column=0, sticky='E')
lowMinBandScanLabel = tk.Label(scanStatusFrame, text="Low Min", fg='blue');
lowMinBandScanLabel.grid(row=3, column=1, sticky='W');

#Baseline
baseBandScanImg = tk.Label(scanStatusFrame, image=imgNotscanned);
baseBandScanImg.grid(row=4, column=1, sticky='E');
baseBandScanLabel = tk.Label(scanStatusFrame, text="Baseline", fg='blue');
baseBandScanLabel.grid(row=4, column=2, sticky='NW', columnspan=2);

#Mid Band Label
midBandScanLabel = tk.Label(scanStatusFrame, text="Mid Band:   ", fg='black');
midBandScanLabel.grid(row=1, column=2, sticky='W', columnspan=2);
#Mid band status
midMaxBandScanImg = tk.Label(scanStatusFrame, image=imgNotscanned);
midMaxBandScanImg.grid(row=2, column=2, sticky='E');
midMaxBandScanLabel = tk.Label(scanStatusFrame, text="Mid Max", fg='blue');
midMaxBandScanLabel.grid(row=2, column=3, sticky='W');
midMinBandScanImg = tk.Label(scanStatusFrame, image=imgNotscanned);
midMinBandScanImg.grid(row=3, column=2, sticky='E')
midMinBandScanLabel = tk.Label(scanStatusFrame, text="Mid Min", fg='blue');
midMinBandScanLabel.grid(row=3, column=3, sticky='W');

#High Band Label
highBandScanLabel = tk.Label(scanStatusFrame, text="High Band:   ", fg='black');
highBandScanLabel.grid(row=1, column=4, sticky='W', columnspan=2);
#High band status
highMaxBandScanImg = tk.Label(scanStatusFrame, image=imgNotscanned);
highMaxBandScanImg.grid(row=2, column=4, sticky='E');
highMaxBandScanLabel = tk.Label(scanStatusFrame, text="High Max", fg='blue');
highMaxBandScanLabel.grid(row=2, column=5, sticky='W');
highMinBandScanImg = tk.Label(scanStatusFrame, image=imgNotscanned);
highMinBandScanImg.grid(row=3, column=4, sticky='E')
highMinBandScanLabel = tk.Label(scanStatusFrame, text="High Min", fg='blue');
highMinBandScanLabel.grid(row=3, column=5, sticky='W');

#Clear button
clearAllButton = tk.Button(scanStatusFrame, text="Clear", bg='red', command=clearAllBands);
clearAllButton.grid(row=4, column=5);

scanStatusFrame.grid(row=5, column=0);

scanButton=tk.Button(ctrl, text='Scan', width=8, command=scan, bg='blue', fg='white');
scanButton.grid(row=5, column=1, sticky='E');

##disableMultibands()

##snEntry = tk.entry

####********** Spacer row
##
##spacerLabel = tk.Label(ctrl, text=" ");
##spacerLabel.grid(row=numrows-3, column=0);

##********** Spacer row

spacerLabel = tk.Label(ctrl, text=" ");
spacerLabel.grid(row=numrows-2, column=0);

##********** Row Last
saveFrame = tk.Frame(ctrl, relief='raised', bd=1)

fileLabel = tk.Label(saveFrame, text="Save file: ", anchor='e');
fileLabel.grid(row=0, column=0);
fileEntry = tk.Entry(saveFrame);
fileEntry.grid(row=0, column=1, sticky='W');

saveButton=tk.Button(saveFrame, text="Save", command=save, bg='green');
saveButton.grid(row=1, column=1, sticky='E');

helpButton=tk.Button(ctrl, text="Help", command=help);
helpButton.grid(row=numrows-1, column=0);

saveFrame.grid(row=numrows-1, column=numcols-1, sticky='SE');

##************* Configure Defaults

scanModeRB2.select(); #Sets scan mode to frequency:non-multiband.
scanModeRB2.invoke(); #  Deactivates multiband UI elements

scaleRB2.select(); #Sets scale to automatic logarithmic
scaleRB2.invoke(); #(Does nothing)

scaleNumberEntry0.insert(0,10) #Set default min freq. to 10Hz
scaleNumberEntry1.insert(0,10) #Set default steps to 10
scaleNumberEntry2.insert(0,20e3) #Set default max freq. to 20KHz


##************** Initialize and launch

initializeTestEquipment();

ctrl.mainloop();

#Disconnect from test equipment when program is finished running
scope.close();
awg.close();
