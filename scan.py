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
#
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
#
#
#
def collectAmpl():
	pass;

def printTable():
	print("-----------------------------------------------------------------------------------------");
	print("|                                   Data Collected                                      |");
	print("-----------------------------------------------------------------------------------------");
	print("|Freq (Hz)\t\t|In (Vpp)\t\t|Out (Vpp)\t\t|Out (V_lvl)\t|");
	print("-----------------------------------------------------------------------------------------");
	for i in range(len(freqs)):
		print("|"+ "{:09.4e}".format(freqs[i]) + "\t\t|" + "{:09.4e}".format(in_vpp[i]) + "\t\t|" + "{:09.4e}".format(out_vpp[i]) + "\t\t|" + "{:09.4e}".format(level_avg[i]) + "\t|");
		print("-----------------------------------------------------------------------------------------");

# Saves the data to a KV1 file
#
#
#
def save():
	fn = raw_input("\tFilename: ");
	hd = raw_input("\tHeader: ");
	if (fn[len(fn)-4:] != ".kv1" and fn[len(fn)-4:] != ".KV1"):
		change_fn = raw_input("Change extension to '.kv1'? Current filename: '" + fn + "'. Change (y/n)? ");
		if (change_fn == 'y' or change_fn == "Y"):
			fn = fn[0:fn.find('.')]+".kv1";
	write_kvar(fn,hd, freqs=freqs, in_vpp=in_vpp, in_rms=in_rms, out_vpp=out_vpp, out_rms=out_rms, level_avg=level_avg);
	saved = True;
