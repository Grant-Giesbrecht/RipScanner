#!/usr/bin/env python

"""
	Download data from a Rigol DS1052E oscilloscope and graph with matplotlib.
	By Ken Shirriff, http://righto.com/rigol
	Based on http://www.cibomahto.com/2010/04/controlling-a-rigol-oscilloscope-using-linux-and-python/
	by Cibo Mahto.
	"""

import numpy
import matplotlib.pyplot as plot
import sys
import visa
from kvar import write_kvar

##********************************************************
##********************** INITIALIZE **********************

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

freqs = [];
in_vpp = [];
in_rms = [];
out_vpp = [];
out_rms = [];
level_avg = [];

saved = True;

noncorrupted_length = 0;

while True:

	cmd = input("> ");
	wrds = cmd.split(" ");
	if (len(wrds) < 1):
		continue;

	if (wrds[0] == "col" or wrds[0] == "c"):

		##*****************************************************************************************##
		##***************************** DATA COLLECTION SUBROUTINE ********************************##
                
#		freqs.append(float(scope.query("MEAS:COUN:VAL?")));
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

                ##*****************************************************************************************##
                ##*************************** END DATA COLLECTION SUBROUTINE ******************************##
				
	elif (wrds[0] == "print" or wrds[0] == "p"):

                ##*****************************************************************************************##
                ##***************************** PRINT TABLE SUBROUTINE ************************************##
                
		print("-----------------------------------------------------------------------------------------");
		print("|                                   Data Collected                                      |");
		print("-----------------------------------------------------------------------------------------");
		print("|Freq (Hz)\t\t|In (Vpp)\t\t|Out (Vpp)\t\t|Out (V_lvl)\t|");
		print("-----------------------------------------------------------------------------------------");
		for i in range(len(freqs)):
			print("|"+ "{:09.4e}".format(freqs[i]) + "\t\t|" + "{:09.4e}".format(in_vpp[i]) + "\t\t|" + "{:09.4e}".format(out_vpp[i]) + "\t\t|" + "{:09.4e}".format(level_avg[i]) + "\t|");
		print("-----------------------------------------------------------------------------------------");

                ##*****************************************************************************************##
                ##*************************** END PRINT TABLE SUBROUTINE **********************************##
		
	elif (wrds[0] == "eraselast" or wrds[0] == "e"):
		freqs.pop();
		in_vpp.pop();
#		in_rms.pop()
#		out_rms.pop();
		out_vpp.pop();
		level_avg.pop();
	elif (wrds[0] == "help" or wrds[0] == "h"):
		print(" --------------- TE108 Help Page --------------- ");
		print("");
		print("Commands:");
		print("\tcol/c: Collect a data point");
		print("\tprint/p: Print all data points");
		print("\teraselast/e: Erase last data point");
		print("\thelp/h: Display help page");
		print("\tsave/s: Save data points to KV1 file");
		#print("\tgraph/g: Graph the data points");
		print("\texit: Exit program");
	elif (wrds[0] == "save" or wrds[0] == "s"):

		##*****************************************************************************************##
		##***************************** SAVE SUBROUTINE ************************************##
                
		fn = raw_input("\tFilename: ");
		hd = raw_input("\tHeader: ");
		if (fn[len(fn)-4:] != ".kv1" and fn[len(fn)-4:] != ".KV1"):
			change_fn = raw_input("Change extension to '.kv1'? Current filename: '" + fn + "'. Change (y/n)? ");
			if (change_fn == 'y' or change_fn == "Y"):
				fn = fn[0:fn.find('.')]+".kv1";
		write_kvar(fn,hd, freqs=freqs, in_vpp=in_vpp, in_rms=in_rms, out_vpp=out_vpp, out_rms=out_rms, level_avg=level_avg);
		saved = True;

		##*****************************************************************************************##
		##*************************** END SAVE SUBROUTINE **********************************##

	elif (wrds[0] == "graph" or wrds[0] == "g"):
		continue;
	elif (wrds[0] == "exit"):
		if (not saved):
			abrt = raw_input("\tUnsaved data will be deleted. Abort quit (y/n)? ");
			if (abrt == 'y' or abrt == "Y"):
				continue;
		break;
	else:
		print("Unrecognized command.");

scope.close();
