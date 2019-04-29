# This program defines functions to read/write KV1 files from python.
#
# KV1 files are a standard designed to make data easily portable
# between programming languages, systems, etc. By allowing comments,
# headers, and variable names inside a standardized data file one is
# able to comment on their data and share it with others in a
# self-explanatory way not possible with simpler formats. Furthermore,
# KV1 files are plain-text & human readible to make extracting the data
# easy even if a library or program designed to read KV1s isn't
# available.
#
#	Created by Grant Giesbrecht on 14.1.2019
#
#	* begin_kvar(), assemble_kvar(), write_kvar() added on 28.4.2019 by
#	  Grant Giesbrecht.
#


# To import functions from this file, put this file in the same
# directory as the program you wish to call this from, then put
# 'from kvar import write_kvar' to import the write_kvar function
# or 'from kvar import *' to import all function
#



# Writes input variables to a KV1 file
#
# Arguments:
#	filename - (string) name of file to write
#	header - (string) header contents. Can be left blank.
#	kwargs - (key-worded arg. list ie. key1=value1, key2=value2)
#		key - What to name variable in KV1 file
#		value - Variable to write to file
#
# Void return
#
# Example Usage:
#		freqs = [1, 2, 3, 4];
#		V = [15, 12, 14, 19];
# 		write_kvar("test.kv1", "", f=freqs, volts=V);
#
def write_kvar(filename, header, **kwargs):

	#Open file & write fixed items
	f = open(filename, "w");
	f.write("#VERSION 1.0\n\n");
	f.write("#HEADER\n");
	f.write(header + "\n");
	f.write("#HEADER\n\n");

	#Write all variables
	for key, value in kwargs.items():
		if (type(value) == list): #If variable is a list...
			if (len(value) < 1): #Ensure list is not empty
				continue;
			if (type(value[0]) == int or type(value[0]) == float): #If list of doubles...
				outstr = "m<d> " + key + " ["; #Initialize variable
				for i in range(len(value)): #Print all values in list
					outstr = outstr + str(value[i]);
					if (i+1 < len(value)):
						outstr = outstr + ", ";
			elif (type(value[0]) == str): #If list of strings...
				outstr = "m<s> " + key + " ["; #Initialize variable
				for i in range(len(value)): #Print all values in list
					outstr = outstr + '"' + value[i] + '"';
					if (i+1 < len(value)):
						outstr = outstr + ", ";
			elif (type(value[0]) == bool): #If list of bools...
				outstr = "m<b> " + key + " ["; #Initialize variable
				for i in range(len(value)): #Print all values in list
					outstr = outstr + str(value[i]);
					if (i+1 < len(value)):
						outstr = outstr + ", ";
			else: #Else unsupported type
				print("Unsupported type for key '" + key + "'\n");
				continue;
			f.write(outstr + "];\n");
		elif (type(value) == int or type(value) == float):
			f.write("d " + key + " " + str(value) + ";\n");
		elif (type(value) == str):
			f.write("s " + key + " "+ '"' + value + '"' +";\n");
		elif (type(value) == bool):
			f.write("b " + key + " " + str(value) + ";\n");
		else:
			print("Unsupported type for key '" + key + "'\n");
			continue;

	f.close();

# Begins a string which can be used to slowly assemble a kvar file (a 'kvstring'). (This is
# handy if you need to assmeble a kvar gradualy, perhaps in a for-loop.) The
# function takes a header string and returns a string which you can feed to
# 'assemble_kvar()' to incrementally assemble a kvar file.
#
# Arguments:
#	header - (string) header contents. Can be left blank ("").
#
# Returns the beginning of a KV1 file string.
#
# Example Usage:
#	V = [[1, 10, 12, 19], [1, 1.13, 1.52, 1.98, 1.43]];
#	kvstring = begin_kvar("This is a header");
#	for idx in range(len(V)):
#		kvstring = assemble_kvar(kvstring, "V"+str(idx), V[idx]);
#	write_assembled_kvar("data.kv1", kvstring);
#
def begin_kvar(header):
	kvs = "#VERSION 1.0\n\n#HEADER\n"+header + "\n#HEADER\n\n";
	return kvs;

# Writes input variable to a string which can be used to write a KV1 file.
#
# Arguments:
#	kvstring - (string) kvstring to which to add variables (ie. a string
#		which can be used to write a kv1 file.
#	key - What to name variable in KV1 file
#	value - Variable to write to file
#
# Returns updated string
#
# Example Usage:
#	V = [[1, 10, 12, 19], [1, 1.13, 1.52, 1.98, 1.43]];
#	kvstring = begin_kvar("This is a header");
#	for idx in range(len(V)):
#		kvstring = assemble_kvar(kvstring, "V"+str(idx), V[idx]);
#	write_assembled_kvar("data.kv1", kvstring);
#
def assemble_kvar(kvstring, key, value):

	#Write variable to kvstring
	if (type(value) == list): #If variable is a list...
		if (len(value) < 1): #Ensure list is not empty
			return;
		if (type(value[0]) == int or type(value[0]) == float): #If list of doubles...
			outstr = "m<d> " + key + " ["; #Initialize variable
			for i in range(len(value)): #Print all values in list
				outstr = outstr + str(value[i]);
				if (i+1 < len(value)):
					outstr = outstr + ", ";
		elif (type(value[0]) == str): #If list of strings...
			outstr = "m<s> " + key + " ["; #Initialize variable
			for i in range(len(value)): #Print all values in list
				outstr = outstr + '"' + value[i] + '"';
				if (i+1 < len(value)):
					outstr = outstr + ", ";
		elif (type(value[0]) == bool): #If list of bools...
			outstr = "m<b> " + key + " ["; #Initialize variable
			for i in range(len(value)): #Print all values in list
				outstr = outstr + str(value[i]);
				if (i+1 < len(value)):
					outstr = outstr + ", ";
		else: #Else unsupported type
			print("Unsupported type for key '" + key + "'\n");
			return kvstring;
		kvstring = kvstring + outstr + "];\n";
	elif (type(value) == int or type(value) == float):
		f.write("d " + key + " " + str(value) + ";\n");
		kvstring = kvstring + "d " + key + " " + str(value) + ";\n";
	elif (type(value) == str):
		f.write("s " + key + " "+ '"' + value + '"' +";\n");
		kvstring = kvstring + "s " + key + " "+ '"' + value + '"' +";\n";
	elif (type(value) == bool):
		f.write("b " + key + " " + str(value) + ";\n");
		kvstring = kvstring + "b " + key + " " + str(value) + ";\n";
	else:
		print("Unsupported type for key '" + key + "'\n");
		return kvstring;

	return kvstring;

# Takes a string containing kv1 data and writes it to a file.
#
# Arguments:
#	filename - (string) name of file to which to write.
#	kvstring - (string) string containing kv1 data.
#
# Void return
#
# Example Usage:
#	V = [[1, 10, 12, 19], [1, 1.13, 1.52, 1.98, 1.43]];
#	kvstring = begin_kvar("This is a header");
#	for idx in range(len(V)):
#		kvstring = assemble_kvar(kvstring, "V"+str(idx), V[idx]);
#	write_assembled_kvar("data.kv1", kvstring);
#
def write_assembled_kvar(filename, kvstring):

	#Open file for writeing
	f = open(filename, "w");
	f.write(kvstring);
	f.close();
