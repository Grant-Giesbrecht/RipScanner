#***************************************************************************************************#
#*********************                        RIP SCANNER                     **********************#
#*********************       CREATED ON 28.4.2019   BY GRANT GIESBRECHT       **********************#
# This program works in conjunction with a Rigol DS2074Z+ oscilloscope and Siglent SDG2042X         #
# arbitrary waveform generator to rapidly and accurately scan transfer functions of circuits. The   #
# program includes a GUI for ease of use, along with a detailed print out of actions to the command #
# line. Python was used because of the simplicity of PyVisa, matplotlib, tkinter, and porting it    #
# across numerous platforms. Although designed for specific scopes, only a dozen or so commands are #
# device specific. Comments next to the SCPI commands describe their purpose - referencing your     #
# device's programming manual should allow you to quickly and easily replace these commands with    #
# those required by your device.                                                                    #
#                                                                                                   #
# Features:                                                                                         #
#   * Automatic Data Integrity and Equilibrium Checker:                                             #
#       Rip Scanner includes an automatic checking facility to ensure that the data received from   #
#       the scope are not corrupt and represent the equilibrium state. It prevents locking if bad   #
#       data are received, prevents incorrect measurements from sabotaging scans, and improves the  #
#       reliability of the system. Furthermore, by advancing to the next scan point upon receiving  #
#       good data, scans are completed much faster than with the old meathod of using a fixed       #
#       delay.                                                                                      #
#                                                                                                   #
#   * Automatic Oscilloscope Scaling:  (Dual-sweep system)                                          #
#       Although the time/div scale can be easily determined for any frequency, the vertical scale  #
#       isn't as well defined. RIP scanner uses a dual-scan technique in which a low vertical       #
#       resolution scan is used to determine the fine vertical resolution of the main scan.         #
#       This system allows for large dynamic ranges of the DUT's output to be captured with ease    #
#       and precision.                                                                              #
#                                                                                                   #
#***************************************************************************************************#

#Import packages

import visa
import sys
import tkinter as tk
from tkinter import messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from time import sleep
import time
from kvar import *
import os

import numpy as np

#*********************************************************#
#*********************** SETTINGS ************************#

#Oscilloscope parameters
numPeaksPerFrame = 10; #No. oscillations to fit on the scope screen when aquiring data
numDivHoriz = 12; #No. horiz. divs on scope screen
numDivVert = 8; #No. vert divs on scope scren
timeWithConstReading = .5; #Time in seconds for reading to stay the same before recording the data point (default: .2) ().5 also good)
maxPercentAccepted = 10; #Maximum percent change allowed while still being considered 'constant' (default: 10) (5 also good)
maxPercentAcceptedFrequencyDelta = 5; #Maximum percent difference allowed between set frequency and measured frequency (to ensure equilibrium) (default: 5)
maxRetryTime = 15; #Maximum time allowed for scan to retry getting a consistant data point (default: 6)

#Vertical Resolution Parameters
vertExpandFactor = 1.5; #factor by which to expand the vertical scale when guessing how to scale vertically (bigger # shrinks signal more, 1 is min). (default: 1.5)
turnOffAfterScan = False; #Turn off the generator after an individaual scan (True for IV-Curves)
setMeasDelay = 700; #Delay in ms between setting the lab instruments to the data point & first measuring the values (to let equilibrium set up) (default: 700)

#Dual-sweep settings
autoDualSweep = True; #When performing an automatic-scaled scan
crudeVertSweepFactor = 2/8; #Algorithm: volts per division = (input_amplitude * crudeVertSweepFactor); (Default: 2) (2/8 for IV-Curves)
fineVertScaleFactor = 1.5; #Factor by which to scale measured amplitude when selecting a fine scale (Default: 1.2) (1.5 for IV-Curves)

#Save settings
saveUntilClear = True; #(If not in multi-band mode) saves TFs until 'Clear' is hit. Saves all when save command given.

#IV settings
shunt_resistance = 100; #Resistance of shunt resistor

voiceAlerts = False;

#*********************************************************#
#*********************************************************#

#Declare sample buffers
freqs = []; #Sample frequencies
ampls = []; #Sample amplitudes

#Define data arrays (multi-band)
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

#Define data arrays (non-multi-band)
fmeas = []; #Freq. buffer
imeas = []; #Input ampl. buffer
omeas = []; #output ampl. buffer
meas3 = []; #CH3 buffer
meas4 = []; #CH4 buffer
saveType = [];

fmeasSave = []; #2D save buffer for fmeas Values
imeasSave = []; #2D save buffer for imeas values
omeasSave = []; #2D save buffer for omeas values
meas3Save = []; #2D save buffer for meas3 values
meas4Save = []; #2D save buffer for meas4 values
dc1Save = []; #2D save buffer for meas3 values
dc2Save = []; #2D save buffer for meas4 values

#Define scale buffers (for dual-auto-sweep)
fineScaleCh2 = []; #Fine-scale buffer (CH1)
fineScaleCh3 = []; #Fine-scale buffer (CH2)
fineScaleCh4 = []; #Fine-scale buffer (CH3)

#These are the global variables modified by the command 'collect()' because I can't use references (because this isn't c++ apparantly :/ )
fr, c1, c2, c3, c4 = 0, 0, 0, 0, 0;

print("General Purpose Transfer Function Scanner");
print("\n**** Copyright 2019, Giesbreceht Electronics ****");

rm = visa.ResourceManager()
# Get the USB device, e.g. 'USB0::0x1AB1::0x0588::DS1ED141904883'
instruments = rm.list_resources()
scope_addr = list(filter(lambda x: 'DS1Z' in x, instruments))
awg_addr = list(filter(lambda x: 'SDG2X' in x, instruments))
if len(scope_addr) != 1 or len(awg_addr) != 1:
    print('Failed to identify test instruments', instruments)
    if (voiceAlerts):
        os.system("say Verbindung zu Testgerat fehlgeschlagen -r 150& &>/dev/null");
    sys.exit(-1)
scope = rm.open_resource(scope_addr[0], timeout=30, chunk_size=1024) # bigger timeout for long mem
print("Connected to scope");
awg = rm.open_resource(awg_addr[0], timeout=30, chunk_size=1024) # bigger timeout for long mem
print("Connected to generator");
if (voiceAlerts):
    os.system("say Verbindung zum Testgerat erfolgreich -r 150& &>/dev/null &");

#Initialize oscilloscope to collect data
#scope.write("MEAS:COUN:SOUR CHAN1");
scope.write("MEAS:STAT:ITEM FREQ,CHAN1");
#scope.write("MEAS:STAT:ITEM VRMS,CHAN1");
#scope.write("MEAS:STAT:ITEM VRMS,CHAN2");
scope.write("MEAS:STAT:ITEM VPP,CHAN1");
scope.write("MEAS:STAT:ITEM VPP,CHAN2");
scope.write("MEAS:STAT:ITEM VPP,CHAN3");
scope.write("MEAS:STAT:ITEM VPP,CHAN4");
# scope.write("MEAS:STAT:ITEM VAVG,CHAN4");

#Set trigger
scope.write("TRIG:EDG:SOUR CHAN1"); #Set trigger source to channel 1
scope.write("TRIG:MODE EDGE") #Set trigger mode to edge
scope.write("TRIG:EDGE:LEV 0") #Set trigger level to 0 V

awg.write("C2:BSWV WVTP,SINE"); #Set AWG to output a sine wave
# awg.write("C2:BSWV WVTP,DC"); #Set AWG to output a DC signal
awg.write("C2:BSWV OFST,0"); #Set DC offset to 0V

#Define Subroutines
##def measVsAmp(fmeas, omeas, imeas, meas3, meas4):
##    fmeas[:] = [12, 50, 100, 330, 1e3, 3.3e3, 20e3];
##    omeas[:] = [1.9, 2.3, 7, 19, 40, 20, 2.4];
##    imeas[:] = [2, 2, 2, 2, 2, 2, 2];
##    pass;

##
## Collect a single data point using input-amplitude as the independent variable
##
##
# def collectAmpl():
#     pass;

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
# Takes a list of values ('rvals') to which to round, and
# Returns the smallest one which is greater than
# or equal to 'x'. 'rvals' must be in least to greatest order.
#
def listCeil(x, rvals):
    for cc in rvals:
        if (x <= cc):
            return cc;
    return max(rvals);
#
# Rounds the number 'x' to the closest oscilloscope 'course'
# scaling value.
#
def courseCeil(x):
    roundVals = [1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1, 2, 5, 10];
    return listCeil(x, roundVals);

#
# Calculates the max percent change between 'a' and 'b' (absolute values). If one is zero and the
# other is non-zero, it returns a change of 1000%.
#
def mpc(a, b):
    a = abs(a);
    b = abs(b);
    if (a-b) == 0:
        return 0;
    if (min(a, b) == 0):
        return 1000;
    return 100.0*abs(a-b)/min(a,b);

#
# Collect a single data point using frequency as the independent variable.
#
#
# def collect(fmeas, imeas, omeas, meas3, meas4):
def collect():
    #Declare buffers
    global fr, c1, c2, c3, c4;

    # fr.append(float(scope.query("MEAS:COUN:VAL?")));
    added = 0;
    try:
        if (scanMode.get() != 3):
            fr = float(scope.query("MEAS:STAT:ITEM? CURR,FREQ,CHAN1"));
            added = 1;
            c1 = float(scope.query("MEAS:STAT:ITEM? CURR,VPP,CHAN1"));
            added = 2;
            #        in_rms.append(float(scope.query("MEAS:STAT:ITEM? CURR,VRMS,CHAN1")));
            c2 = float(scope.query("MEAS:STAT:ITEM? CURR,VPP,CHAN2"));
            added = 3;
            #        out_rms.append(float(scope.query("MEAS:STAT:ITEM? CURR,VRMS,CHAN2")));
            if (ch3on.get() == 1):
                c3 = float(scope.query("MEAS:STAT:ITEM? CURR,VPP,CHAN3"));
            added = 4;
            if (ch4on.get() == 1):
                c4 = float(scope.query("MEAS:STAT:ITEM? CURR,VPP,CHAN4"));
            added = 5;
        else:
            fr = 0;
            added = 1;
            c1 = float(scope.query("MEAS:STAT:ITEM? CURR,VAVG,CHAN1"));
            added = 2;
            #        in_rms.append(float(scope.query("MEAS:STAT:ITEM? CURR,VRMS,CHAN1")));
            c2 = float(scope.query("MEAS:STAT:ITEM? CURR,VAVG,CHAN2"));
            added = 3;
            #        out_rms.append(float(scope.query("MEAS:STAT:ITEM? CURR,VRMS,CHAN2")));
            if (ch3on.get() == 1):
                c3 = float(scope.query("MEAS:STAT:ITEM? CURR,VPP,CHAN3"));
            added = 4;
            if (ch4on.get() == 1):
                c4 = float(scope.query("MEAS:STAT:ITEM? CURR,VPP,CHAN4"));
            added = 5;
        #            print("\t** f = " + "{:09.4e}".format(freqs[i]) + " Hz\t**\tVin = " + "{:09.4e}".format(in_vpp[i]) + " Vpp\t" + "{:09.4e}".format(in_rms[i]) + " Vrms\t**\tVout = " + "{:09.4e}".format(out_vpp[i]) + " Vpp\t" + "{:09.4e}".format(out_rms[i]) + "Vrms\t**\tVlevel = " + "{:09.4e}".format(level_avg[i]) + "V");
        print("\t** f = " + "{:09.4e}".format(fr) + " Hz\t**\tVin = " + "{:09.4e}".format(c1) + " Vpp\t**\tVout = " + "{:09.4e}".format(c2) + " Vpp\t**\tVc3 = " + "{:09.4e}".format(c3) + "V" + " Vpp\t**\tVc4 = " + "{:09.4e}".format(c4) + "V");
    except Exception as e:
        # print("Failed to collect data point. Fixing ");
        #
        # while (len(freqs) > noncorrupted_length):
        #     del freqs[noncorrupted_length];
        #
        # while (len(in_vpp) > noncorrupted_length):
        #     del in_vpp[noncorrupted_length];
        #
        # while (len(in_rms) > noncorrupted_length):
        #     del in_rms[noncorrupted_length];
        #
        # while (len(out_vpp) > noncorrupted_length):
        #     del out_vpp[noncorrupted_length];
        #
        # while (len(out_rms) > noncorrupted_length):
        #     del out_rms[noncorrupted_length];
        #
        # while (len(level_avg) > noncorrupted_length):
        #     del level_avg[noncorrupted_length];

        print("Measurement error (" + str(added) + "). Point not recorded.");
        print("\t"+str(e));
        return False;

    #Ensure data are valid...
    if (fr > 1e30 or c1 > 1e30 or c2 > 1e30 or c3 > 1e30 or c4 > 1e30):
        print("Received invalid data.");
        return False;



    # fmeas.append(fr);
    # imeas.append(c1);
    # omeas.append(c2);
    # meas3.append(c3);
    # meas4.append(c4);

    return True;

#
# Takes the data collected from the first crude-scan and calculates the fine-resolution
# vertical-scales to be used in the second scan.
#
def getFineScale(fmeas, imeas, omeas, meas3, meas4):

    global fineScaleCh2, fineScaleCh3, fineScaleCh4;

    print("Calculating fine scales...");

    fineScaleCh2 = [];
    fineScaleCh3 = [];
    fineScaleCh4 = [];

    for idx in range(len(fmeas)): #For each sample point...
        fineScaleCh2.append(courseCeil(omeas[idx]/numDivVert*fineVertScaleFactor)); #Get vert. scale that fits the measured amplitude (plus a little extra)
        print("FS start value: "+str(omeas[idx]));
        print("FS Added: " +str(courseCeil(omeas[idx]/numDivVert*fineVertScaleFactor)));
        if (ch3on.get() == 1):
            fineScaleCh3.append(courseCeil(meas3[idx]/numDivVert*fineVertScaleFactor)); #Get vert. scale that fits the measured amplitude (plus a little extra)
        if (ch4on.get() == 1):
            fineScaleCh4.append(courseCeil(meas4[idx]/numDivVert*fineVertScaleFactor)); #Get vert. scale that fits the measured amplitude (plus a little extra)

    return True;
#
# Measure a transfer function (using 1+ data points).
#
#
def meas(fmeas, imeas, omeas, meas3, meas4, crudeSweep):

    firstPoint = True;

    amplitude = 1;


    #Make sure initial amplitude doesn't fry anything
    if (len(freqs) > 0 and scanMode.get() != 3):
        awg.write("C2:BSWV AMP,"+str(ampls[0]));
    elif (len(freqs) > 0):
        awg.write("C2:BSWV OFST,"+str(ampls[0]));

    #Turn on generator
    awg.write("C2:OUTP ON");

    for idx in range(len(freqs)):

        #Set frequency
        if (scanMode.get() != 3):
            awg.write("C2:BSWV FRQ,"+str(freqs[idx]))
            print("SCPI<AWG> C2:BSWV FRQ,"+str(freqs[idx]));

        #Set amplitude
        if (scanMode.get() != 3): #VPP Amplitude
            awg.write("C2:BSWV AMP,"+str(ampls[idx]));
            print("SCPI<AWG> C2:BSWV AMP,"+str(ampls[idx]));
        else:
            awg.write("C2:BSWV OFST,"+str(ampls[idx]));
            print("SCPI<AWG> C2:BSWV OFST,"+str(ampls[idx]));

        #Configure scope settings
        if (aquisitionMode.get() == 0): #Automatic

            #Determine time/div setting
            totalTime = 1/freqs[idx]*numPeaksPerFrame;
            timePerDiv = totalTime/numDivHoriz;
            scope.write("TIM:MAIN:SCAL "+str(timePerDiv));
            print("SCPI<SCOPE> TIM:MAIN:SCAL "+str(timePerDiv));

            #********** Determine volts/div setting

            #Channel 1 always a function of input amplitude
            if (scanMode.get() != 3):
                voltsPerDiv = courseCeil(ampls[idx]/numDivVert*vertExpandFactor);
                scope.write("CHAN1:SCAL "+str(voltsPerDiv));
                print("SCPI<SCOPE> CHAN1:SCAL "+str(voltsPerDiv));
            else:
                voltsPerDiv = courseCeil(ampls[idx]*2/numDivVert*vertExpandFactor); #Mult ampl by 2 b/c only using half the scale
                scope.write("CHAN1:SCAL "+str(voltsPerDiv));
                print("SCPI<SCOPE> CHAN1:SCAL "+str(voltsPerDiv));

            #Iteratively select scale for CH2, 3, 4
            if (autoDualSweep == True): #If dual-sweep... (ie. set to auto vertical scale (!from file) and dual-sweep is on)
                if (crudeSweep): #If performing crudeSweep, voltsPerDiv for every channel is just scaled up greatly from CH1 scale.

                    voltsPerDiv = 0;
                    if (scanMode.get() != 3):
                        voltsPerDiv = courseCeil(ampls[idx]*crudeVertSweepFactor);
                    else:
                        voltsPerDiv = courseCeil(ampls[idx]*2*crudeVertSweepFactor); #Mult ampl by 2 b/c only using half the scale
                        print(str(ampls[idx]) + " * 2 * " + str(crudeVertSweepFactor));

                    scope.write("CHAN2:SCAL "+str(voltsPerDiv));
                    print("SCPI<SCOPE> CHAN2:SCAL "+str(voltsPerDiv));
                    if (ch3on.get() == 1):
                        scope.write("CHAN3:SCAL "+str(voltsPerDiv));
                        print("SCPI<SCOPE> CHAN3:SCAL "+str(voltsPerDiv));
                    if (ch4on.get() == 1):
                        scope.write("CHAN4:SCAL "+str(voltsPerDiv));
                        print("SCPI<SCOPE> CHAN4:SCAL "+str(voltsPerDiv));
                else: #Performing fine-sweep. Use channel vert-scales from list 'fineScaleChX'
                    if (len(fineScaleCh2) < 1):
                        print("Fine scale list is unpopulated!");
                        return False;

                    if (scanMode.get() != 3):
                        scope.write("CHAN2:SCAL "+str(fineScaleCh2[idx]));
                        print("SCPI<SCOPE> CHAN2:SCAL "+str(fineScaleCh2[idx]));
                    else:
                        scope.write("CHAN2:SCAL "+str(fineScaleCh2[idx]*2)); #Mult ampl by two b/c only using half the scale
                        print("SCPI<SCOPE> CHAN2:SCAL "+str(fineScaleCh2[idx]*2)); #Mult ampl by two b/c only using half the scale
                    if (ch3on.get() == 1):
                        scope.write("CHAN3:SCAL "+str(fineScaleCh3[idx]));
                        print("SCPI<SCOPE> CHAN3:SCAL "+str(fineScaleCh3[idx]));
                    if (ch4on.get() == 1):
                        scope.write("CHAN4:SCAL "+str(fineScaleCh4[idx]));
                        print("SCPI<SCOPE> CHAN4:SCAL "+str(fineScaleCh4[idx]));
                    if (str(fineScaleCh2[idx]) == "None"):
                        print("Error occured w/ vert scale being called 'none'. Length of fsc2: "+str(len(fineScaleCh2)));

            else: #using guess method that is somewhat arbitrary (mult. by a fixed coef. to get scale)
                if (firstPoint): #guess it's about the size of the input if no idea
                    scope.write("CHAN2:SCAL "+str(voltsPerDiv));
                    print("SCPI<SCOPE> CHAN2:SCAL "+str(voltsPerDiv));
                    if (ch3on.get() == 1):
                        pass;
                        scope.write("CHAN3:SCAL "+str(voltsPerDiv));
                        print("SCPI<SCOPE> CHAN3:SCAL "+str(voltsPerDiv));
                    if (ch4on.get() == 1):
                        scope.write("CHAN4:SCAL "+str(voltsPerDiv));
                        print("SCPI<SCOPE> CHAN4:SCAL "+str(voltsPerDiv));



        else: #From file
            print("Aquisition settings from file not yet suppored.");
            return False;


        #**********************************************************************************#
        #*********************  DATA INTEGRITY AND EQUILIBRIUM CHECKER ********************#
        # The introduction of this code accelerated the scan speed dramatically because it #
        # eliminated the need to wait a fixed time to establish equilibrium. These fixed   #
        # times were inordinately large to help even the slowest sample points to scan, but#
        # failures were not uncommon. The boost to data reliability and elimination of     #
        # corrupt data has made the program far faster, more accurate, and reliable. NICE. #
        #**********************************************************************************#
        #                                                                                  #
        # Looks for:                                                                       #
        #   - Corrupt data from scope (ie. value > 1e30)                                   #
        #   - Measured and set frequency don't match (Added 5.5.2019)                      #
        #   - Value changes too quickly (not at equilibrium)                               #
        #                                                                                  #
        #**********************************************************************************#

        #Read everything and check for equilibrium and data integrity
        num_failed = 0;
        start = time.time(); #Get total time req'd for data point
        sleep(setMeasDelay*1e-3); #Initial pause to let everything equilibrate
        oldf = 0;
        oldi = 0;
        oldo = 0;
        old3 = 0;
        old4 = 0;
        verifying = False; #Specifies if it's collected a first point or verifying that point w/ a second measurement.
        total_no_scans = 0;
        while (True): #continue trying until accurate readings are had...
            total_no_scans += 1;
            #Take a measurement. If it fails (an exception occurs or data > 1e30 (corrupted)), increment num_failed
            if (not collect()): #Results of collect() are saved in global variables fr, c1, c2, c3, c4 because I can't pass by reference variables :(. Collect will return false if bad/corrupt data is received (value will be > 1e30).
                num_failed += 1;
                sleep(.333); #Wait 100 ms
                if (num_failed > 15): #Cancel scan if too many attempts fail (Takes a maximum of 5 seconds to fail + initial delay)
                    print("Failed to collect all data points successfully.");
                    return False;
            else: #Measurement didn'throw an error or give corrupted data
                num_failed = 0; #Reset fail counter
                if (verifying):

                    #Get max error (and ignore freq if I-V curve)
                    if (scanMode.get() != 3):
                        dval = max(mpc(oldf, fr), mpc(oldi, c1), mpc(oldo, c2), mpc(old3, c3), mpc(old4, c4));
                    else:
                        dval = max(mpc(oldi, c1), mpc(oldo, c2), mpc(old3, c3), mpc(old4, c4));
                    if (dval <= maxPercentAccepted):
                        print("Passed scan No. " + str(total_no_scans) + " with an error of " + str(dval) + " %. Tot. elapsed time: " + str(time.time()-start) + " sec");
                        break; #The measurement has satisfied the subroutine's integrity check
                    else: #The measurement was too far off from the original measurement, try again
                        oldf = fr; #Update the measurements...
                        oldi = c1;
                        oldo = c2;
                        old3 = c3;
                        old4 = c4;
                        print("The measurement, although non-corrupt, failed the equilibrium+integrity check.");
                        print("\tAfter ~" + str(timeWithConstReading) + " seconds, % change: " + str(dval));
                        print("\tTET: "+str(time.time()-start));
                        if (time.time() - start > maxRetryTime):
                            print("Measurement retry time expired. Aborting scan.");
                            return False;
                        sleep(timeWithConstReading); #Wait a bit...
                else:
                    if (scanMode.get() !=3 and mpc(fr, freqs[idx]) > maxPercentAcceptedFrequencyDelta): #Ensure measured and set frequencies match (within a certain margin of error)
                        print("The measurement, although non-corrupt, failed the equilibrium+integrity check.");
                        print("\tFrequency was out of spec. Set: " + str(freqs[idx]) + " Hz \tMeas: " + str(fr) + " Hz");
                        print("\tTET: "+str(time.time()-start));
                        if (time.time() - start > maxRetryTime):
                            print("Measurement retry time expired. Aborting scan.");
                            return False;
                        sleep(timeWithConstReading); #Wait a bit...
                        continue;
                    verifying = True;
                    oldf = fr;
                    oldi = c1;
                    oldo = c2;
                    old3 = c3;
                    old4 = c4;

                    sleep(timeWithConstReading); #Wait a bit...

        #Once past the data integrity+equilibrium check, append to the list
        fmeas.append(fr);
        imeas.append(c1);
        omeas.append(c2);
        meas3.append(c3);
        meas4.append(c4);

        #**********************************************************************************#
        #*****************  END of DATA INTEGRITY AND EQUILIBRIUM CHECKER *****************#
        #**********************************************************************************#

        # if (aquisitionMode.get() == 0):
        #     pass;
        #For each channel...
            #See if last value was > 1000...
                #If so...
                    #set boolean so all last get poped.
                    #Increase vertical scale by a constant




        # if (scanMode.get() == 0): #Amplitude mode
        #     # fmeas[:], imeas[:], omeas[:], meas3[:], meas4[:] = collectAmpl();
        #     pass;
        # else: #Frequency mode
        #     # fmeas[:], imeas[:], omeas[:], meas3[:], meas4[:] = collectFreq();
        #     pass;

    if (turnOffAfterScan):
        awg.write("C2:OUTP OFF");

    # scope.write();

    return True;


#
# Processes everything for a scan. Reads info from the GUI, files, etc. and
# begins a scan (using the meas() function, which in turn, makes multiple calls
# to collectFreq() or collectAmpl()).
#
def scan():
    global plot
    global fmeasSave, imeasSave, omeasSave, meas3Save, meas4Save
    global fmeas, imeas, omeas, meas3, meas4
    global lxi,lxo,lxf,lx3, lx4,lni,lno,lnf,ln3,ln4,mxi,mxo,mxf,mx3,mx4,mni
    global mno,mnf,mn3,mn4,hxi,hxo,hxf,hx3,hx4,hni,hno,hnf,hn3,hn4
    global basei,baseo,basef,base3,base4

    #Get sample frequencies/amplitudes
    if (not getSampleFreqsAmpls()):
        tk.messagebox.showerror("Scan Failed!", "Failed to determine sample frequencies/amplitudes");
        return False;

    print("Frequencies to measure: (Hz)" + str(freqs));

    #Clear buffers
    fmeas = [];
    omeas = [];
    imeas = [];
    meas3 = [];
    meas4 = [];

    scan_start = time.time();

    #Perform measurements (If set to auto-vertical scale dual-auto-sweep, this will be the crude sweep)
    if (not meas(fmeas, imeas, omeas, meas3, meas4, True)): #'True' says to do the crude-sweep. This will be ignored if not in automatic & dual-sweep modes.
        # os.system("say Scan fehlgeschlagen -r 150& &>/dev/null &");
        tk.messagebox.showerror("Scan Failed!", "Failed to complete measurements.");
        return False;



    #Zero-in on vertical-scale if set to dual-sweep
    if (aquisitionMode.get() == 0 and autoDualSweep == True): #If set to auto vertical scale (!from file) and dual-sweep is on...
        print("Course-scan completed successfully.");
        if (not getFineScale(fmeas, imeas, omeas, meas3, meas4)): #Get fine-res sample freqs/ampls
            # os.system("say Scan fehlgeschlagen -r 150& &>/dev/null &");
            tk.messagebox.showerror("Scan Failed!", "Failed to determine fine-resolution vertical scales.");
            return False;

        #Clear buffers
        fmeas =[];
        omeas = [];
        imeas = [];
        meas3 = [];
        meas4 = [];

        if (not meas(fmeas, imeas, omeas, meas3, meas4, False)): #'False' says to do the fine-sweep.
            # os.system("say Scan fehlgeschlagen -r 150& &>/dev/null &");
            tk.messagebox.showerror("Scan Failed!", "Failed to complete fine-resolution measurements.");
            return False;
        print("Fine-resolution scan completed successfully.");
    else:
        print("Scan completed successfully.");

    duration = (time.time() - scan_start);
    if (voiceAlerts):
        os.system("say Scan abgeschlossen.     "+ str(len(fmeas)) + " Punkte in " + str(round(duration)) + " Sekunden gescannt -r 150& &>/dev/null");
        "19 Punkte in 5 Sekunden gescannt"

    print("Scan time: " + str(duration) + " sec");

    #Add to graph
    if (scanMode.get() == 0):
        plot.plot(imeas, omeas, linestyle='dashed', marker='o', markersize=3);
        print("Plotting:")
        print("\tInputs: " + str(imeas));
        print("\tOutputs:" + str(omeas));
    elif(scanMode.get() == 1):
        gains = np.multiply(20, np.log10(np.divide(omeas, imeas))).tolist();
        plot.semilogx(fmeas, gains, linestyle='dashed', marker='o', markersize=3)
        print("Plotting:")
        print("\tFreqs: " + str(fmeas));
        print("\tGains:" + str(gains));
    elif(scanMode.get() == 3):
        for i in range(len(omeas)):
            imeas[i] = imeas[i] - omeas[i]; #Account for voltage across shunt resistor
            omeas[i] = omeas[i]*shunt_resistance; #Convert to current w/ shunt resistance
        plot.plot(imeas, omeas, linestyle='dashed', marker='o', markersize=3);
        print("Plotting:")
        print("\tInputs: " + str(imeas));
        print("\tOutputs:" + str(omeas));


    #Save results
    if (scanMode.get() == 3):
        saveType.append("VAVG");
    else:
        saveType.append("VPP");
    if (scanMode.get() == 0 or scanMode.get() == 1 or scanMode.get() == 3):

        #Clear save buffers if not saving old...
        if (not saveUntilClear):
            print("Wiping last data set");
            fmeasSave = [];
            imeasSave = [];
            omeasSave = [];
            meas3Save = [];
            meas4Save = [];

        #Append results to save buffers
        fmeasSave.append(fmeas);
        imeasSave.append(imeas);
        omeasSave.append(omeas);
        meas3Save.append(meas3);
        meas4Save.append(meas4);



    #Get band & gain & update status panels
    elif (scanMode.get() == 2): #Only if multiband update status panels
        if band.get() == 0:
            bandstr = "Low";
            if gain.get() == 0:
                gainstr = "Min";
                lowMinBandScanImg.configure(image=imgScanned);
                lnf = fmeas;
                lni = imeas;
                lno = omeas;
                ln3 = meas3;
                ln4 = meas4;
            elif gain.get() == 1:
                gainstr = "Max";
                lowMaxBandScanImg.configure(image=imgScanned);
                lxf = fmeas;
                lxi = imeas;
                lxo = omeas;
                lx3 = meas3;
                lx4 = meas4;
            elif gain.get() == 2:
                gainstr = "Flat";
                baseBandScanImg.configure(image=imgScanned);
                basef = fmeas;
                basei = imeas;
                baseo = omeas;
                base3 = meas3;
                base4 = meas4;
            else:
                gainstr = "ERROR ("+str(gain)+")";
        elif band.get() == 1:
            bandstr = "Mid";
            if gain.get() == 0:
                gainstr = "Min";
                midMinBandScanImg.configure(image=imgScanned);
                mnf = fmeas;
                mni = imeas;
                mno = omeas;
                mn3 = meas3;
                mn4 = meas4;
            elif gain.get() == 1:
                gainstr = "Max";
                midMaxBandScanImg.configure(image=imgScanned);
                mxf = fmeas;
                mxi = imeas;
                mxo = omeas;
                mx3 = meas3;
                mx4 = meas4;
            elif gain.get() == 2:
                gainstr = "Flat";
                baseBandScanImg.configure(image=imgScanned);
                basef = fmeas;
                basei = imeas;
                baseo = omeas;
                base3 = meas3;
                base4 = meas4;
            else:
                gainstr = "ERROR ("+str(gain)+")";
        elif band.get() == 2:
            bandstr = "High";
            if gain.get() == 0:
                gainstr = "Min";
                highMinBandScanImg.configure(image=imgScanned);
                hnf = fmeas;
                hni = imeas;
                hno = omeas;
                hn3 = meas3;
                hn4 = meas4;
            elif gain.get() == 1:
                gainstr = "Max";
                highMaxBandScanImg.configure(image=imgScanned);
                hxf = fmeas;
                hxi = imeas;
                hxo = omeas;
                hx3 = meas3;
                hx4 = meas4;
            elif gain.get() == 2:
                gainstr = "Flat";
                baseBandScanImg.configure(image=imgScanned);
                basef = fmeas;
                basei = imeas;
                baseo = omeas;
                base3 = meas3;
                base4 = meas4;
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
            print("From 1e" + str(a) + " to 1e" + str(b) + " in " + str(steps));
            freqs = np.linspace(a, b, c);
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

        amp_dflt = 0;
        try:
            amp_dflt = float(genNumberEntry0.get())
        except:
            print("Failed to read amplitude entry");
            return False;
        ampls = [];
        for i in range(len(freqs)):
            ampls.append(amp_dflt);

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
            fstr = fstr+ str(round(f, 3)) + " ";
        print("Amplitudes: " + fstr)

        freq_dflt = 0;
        try:
            freq_dflt = float(genListEntry.get());
        except:
            print("Failed to read amplitude entry");
            return False;
        freqs = [];
        for i in range(len(ampls)):
            freqs.append(freq_dflt);



    return True

def save():

    #Get header & filename. Check extension
    fn = fileEntry.get();
    hd = headerEntry.get();
    if (fn[len(fn)-4:] != ".kv1" and fn[len(fn)-4:] != ".KV1"): #If not KV1 extension...
        if (tk.messagebox.askyesno("File Extension", "Change extension to KV1? Currrent filename: "+ fn)): #Ask if to change
            if (fn.find('.') != -1):
                fn = fn[0:fn.find('.')]+".kv1";
            else:
                fn = fn + ".kv1";

    #Write data
    if (scanMode.get() == 0 or scanMode.get() == 1): #If not a multiband mode...
        if (saveUntilClear): #If multiple sets of data allowed...
            print("Saving all TFs");
            kvs = begin_kvar(hd); #Create the kvar string
            for idx in range(len(fmeasSave)): #For each batch of data...
                kvs = assemble_kvar(kvs, "freqs"+str(idx), fmeasSave[idx]); #Save freq. array
                kvs = assemble_kvar(kvs, "in_vpp"+str(idx), imeasSave[idx]); #Save input data array
                kvs = assemble_kvar(kvs, "out_vpp"+str(idx), omeasSave[idx]); #Save output data array
                kvs = assemble_kvar(kvs, "ch3_vpp"+str(idx), meas3Save[idx]); #Save ch3 data array
                kvs = assemble_kvar(kvs, "ch4_vpp"+str(idx), meas4Save[idx]); #Save ch4 data array
            write_assembled_kvar(fn, kvs);
            print("Wrote: "+kvs);
        else:
            print("Saving last TF");
            try:
                write_kvar(fn,hd, freqs=fmeasSave[0], in_vpp=imeasSave[0], out_vpp=omeasSave[0], ch3_vpp=meas3Save[0], ch4_vpp=meas4Save[0]);
            except Exception as e:
                print("Failed to save data.");
                print("\t"+str(e));
                return;
    elif (scanMode.get() == 3): #If not a multiband mode...
        if (saveUntilClear): #If multiple sets of data allowed...
            print("Saving all TFs");
            kvs = begin_kvar(hd); #Create the kvar string
            for idx in range(len(fmeasSave)): #For each batch of data...
                kvs = assemble_kvar(kvs, "freqs"+str(idx), fmeasSave[idx]); #Save freq. array
                kvs = assemble_kvar(kvs, "V_vavg"+str(idx), imeasSave[idx]); #Save input data array
                kvs = assemble_kvar(kvs, "I_vavg"+str(idx), omeasSave[idx]); #Save output data array
                kvs = assemble_kvar(kvs, "ch3_vpp"+str(idx), meas3Save[idx]); #Save ch3 data array
                kvs = assemble_kvar(kvs, "ch4_vpp"+str(idx), meas4Save[idx]); #Save ch4 data array
                kvs = assemble_kvar(kvs, "Rshunt"+str(idx), shunt_resistance); #Save shunt resistance used
            write_assembled_kvar(fn, kvs);
            print("Wrote: "+kvs);
        else:
            print("Saving last TF");
            try:
                write_kvar(fn,hd, freqs=fmeasSave[0], in_vpp=imeasSave[0], out_vpp=omeasSave[0], ch3_vpp=meas3Save[0], ch4_vpp=meas4Save[0]);
            except Exception as e:
                print("Failed to save data.");
                print("\t"+str(e));
                return;
    else: #Multiband
        print("Oh no! This isn't implimented yet!");
        return;
        pass;
    print("Data saved.");

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
    # plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [25, 18, 14, 6, 2, 1, .1]);
    ##    plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [1, 13, 14, 26, 16, 12, 1.5], color='green', marker='o', linestyle='dashed', linewidth=1, markersize=3);
    ##    ##plot.cla();
    ##    plot.semilogx([10, 33, 100, 330, 1e3, 3.3e3, 20e3], [1, 0, 1.6, 2, 2.5, 16, 22]);
    if (scanMode.get() == 0):
        plot.set_xlabel("Input Amplitude (Vpp)");
        plot.set_ylabel("Output Amplitude (Vpp)");
        # plot.set_ylim(0, 10);
        # plot.set_xlim(0, 10);
        plot.set_title("Transfer Function");
    elif (scanMode.get() == 3):
        plot.set_xlabel("Voltage (V DC)");
        plot.set_ylabel("Current (A)");
        plot.set_title("I-V Curve");
    else:
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

def setScan3():
    disableMultibands();
    setToIVMode();

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

def setToIVMode():
    scope.write("CHAN1:COUP DC");
    scope.write("CHAN2:COUP DC");
    scope.write("TRIG:SWE AUTO");
    scope.write("MEAS:STAT:ITEM VAVG,CHAN1"); #Measure VPP
    scope.write("MEAS:STAT:ITEM VAVG,CHAN2"); #Measure VPP
    awg.write("C2:BSWV WVTP,DC"); #Set AWG to output a DC signal
    awg.write("C2:BSWV OFST,0"); #Set DC offset to 0V
    scaleNumberLabel0.configure(text='Start (V DC):');
    scaleNumberLabel2.configure(text='End (V DC):');

    if (float(scaleNumberEntry0.get()) > 5):
        scaleNumberEntry0.delete(0, 'end');
        scaleNumberEntry0.insert(0,.1) #Set default min freq. to 10Hz

    if (float(scaleNumberEntry2.get()) > 20):
        scaleNumberEntry2.delete(0, 'end');
        scaleNumberEntry2.insert(0,5) #Set default min freq. to 10Hz

def setToFreqMode():
    scope.write("TRIG:SWE NORM");
    scope.write("MEAS:STAT:ITEM FREQ,CHAN1");
    scope.write("MEAS:STAT:ITEM VPP,CHAN1");
    scope.write("MEAS:STAT:ITEM VPP,CHAN2");
    scope.write("MEAS:STAT:ITEM VPP,CHAN3");
    scope.write("MEAS:STAT:ITEM VPP,CHAN4");
    awg.write("C2:BSWV WVTP,SINE"); #Set AWG to output a sine wave
    awg.write("C2:BSWV OFST,0"); #Set DC offset to 0V
    scaleNumberLabel0.configure(text='Start (Hz):');
    scaleNumberLabel2.configure(text='End (Hz):');

    # if (float(scaleNumberEntry0.get()) < 1):
    #     scaleNumberEntry0.delete(0, 'end');
    #     scaleNumberEntry0.insert(0,10) #Set default min freq. to 10Hz
    #
    # if (float(scaleNumberEntry2.get()) < 20):
    #     scaleNumberEntry2.delete(0, 'end');
    #     scaleNumberEntry2.insert(0,20e3) #Set default min freq. to 10Hz

def setToAmplMode():
    scope.write("TRIG:SWE NORM");
    scope.write("MEAS:STAT:ITEM FREQ,CHAN1");
    scope.write("MEAS:STAT:ITEM VPP,CHAN1");
    scope.write("MEAS:STAT:ITEM VPP,CHAN2");
    scope.write("MEAS:STAT:ITEM VPP,CHAN3");
    scope.write("MEAS:STAT:ITEM VPP,CHAN4");
    awg.write("C2:BSWV WVTP,SINE"); #Set AWG to output a sine wave
    awg.write("C2:BSWV OFST,0"); #Set DC offset to 0V
    scaleNumberLabel0.configure(text='Start (Vpp):');
    scaleNumberLabel2.configure(text='End (Vpp):');

    if (float(scaleNumberEntry0.get()) > 5):
        scaleNumberEntry0.delete(0, 'end');
        scaleNumberEntry0.insert(0,.1) #Set default min freq. to 10Hz

    if (float(scaleNumberEntry2.get()) > 20):
        scaleNumberEntry2.delete(0, 'end');
        scaleNumberEntry2.insert(0,5) #Set default min freq. to 10Hz

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
scanModeRB3 = tk.Radiobutton(modeFrame, text="I-V Curve", variable=scanMode, value=3, command=setScan3);
scanModeRB3.grid(row=1, column=2, stick='W');
scanModeRB2 = tk.Radiobutton(modeFrame, text="Freq.", variable=scanMode, value=1, command=setScan1);
scanModeRB2.grid(row=1, column=3, stick='W');
scanModeRB3 = tk.Radiobutton(modeFrame, text="Freq. (multi-band)", variable=scanMode, value=2, command=setScan2);
scanModeRB3.grid(row=1, column=4, stick='W');


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
graph = Figure(figsize=(5.5,4.5), dpi=100); #Was 6,5 on ubuntu, then 6.5, 5.5 on ubuntu for more space. -> 5.5, 4.5 on mac. dpi was 100 on ubuntu and mac
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
genNumberLabel1 = tk.Label(genNumberFrame, text="Default ampl. (Vpp):"); #Was "Min ampl. (Vpp)". NOTE: This was going to allow dynamic ranging of the input amplitude
genNumberLabel1.grid(row=0, column=0, sticky='W');
# genNumberLabel2 = tk.Label(genNumberFrame, text="Max ampl. (-):"); #NOTE: This was going to allow dynamic ranging of the input amplitude
# genNumberLabel2.grid(row=0, column=1); #NOTE: This was going to allow dynamic ranging of the input amplitude
##genNumberDec = tk.Button(genNumberFrame, text="Decr.", command=genNumberDecrement);
##genNumberDec.grid(row=1, column=0);
genNumberEntry0 = tk.Entry(genNumberFrame, width=13);
genNumberEntry0.grid(row=1, column=0, sticky='W');
# genNumberEntry1 = tk.Entry(genNumberFrame, width=13); #NOTE: This was going to allow dynamic ranging of the input amplitude
# genNumberEntry1.grid(row=1, column=1); #NOTE: This was going to allow dynamic ranging of the input amplitude
##genNumberEntry2 = tk.Entry(genNumberFrame, width=10);
##genNumberEntry2.grid(row=1, column=2);
##genNumberIncr = tk.Button(genNumberFrame, text="Incr.", command=genNumberIncrement);
##genNumberIncr.grid(row=1, column=2);
genNumberFrame.grid(row=1, column=1, rowspan=2, columnspan=2, sticky='W');

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

fileLabel = tk.Label(saveFrame, text="Save file:", anchor='e');
fileLabel.grid(row=0, column=0);
fileEntry = tk.Entry(saveFrame);
fileEntry.grid(row=0, column=1, sticky='W');

headerLabel = tk.Label(saveFrame, text="Header:", anchor='e');
headerLabel.grid(row=1, column=0);
headerEntry = tk.Entry(saveFrame);
headerEntry.grid(row=1, column=1, sticky='W');

saveButton=tk.Button(saveFrame, text="Save", command=save, bg='green');
saveButton.grid(row=0, column=2, sticky='E');

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

genNumberEntry0.insert(0, 1); #Set default amplitude to 1 Vpp
genListEntry.insert(0, 1e3); #Set default frequency to 1KHz
##************** Initialize and launch

ctrl.mainloop();

#Disconnect from test equipment when program is finished running
scope.close();
awg.close();
