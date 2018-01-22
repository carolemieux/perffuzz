from __future__ import print_function
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
#import matplotlib
import re


matplotlib.rcParams.update({'font.size':'14'})

CI_mult = [12.7062,4.3027,3.1824,2.7764,2.5706,2.4469,2.3646, 2.3060, 2.2622,2.2281,2.2010,2.1788,2.1604,2.1448, 2.131,2.120,2.110,2.101,2.093,2.086,2.080,2.074,2.069]

color_cycle=["#999999", "#E69F00", "#009E73",  "#0072B2"]
line_cycle=[":", "-.", "--", '-']

names = []
folder_prefixes = []
folder_suffixes = []
all_counts = {}

# returns two lists: time elapsed -> number of inputs generated
def parse_num_inputs_afl(f):
	raw_times = []
	raw_num_inputs = []
	for line in f:
		line = line.rstrip()
		if not line.startswith("#"):
			split_line = line.split(",")
			raw_times.append(int(split_line[0]))
			raw_num_inputs.append((int(split_line[3]), int(split_line[7]), int(split_line[8])))
	start_time = raw_times[0]
	relative_times = [t - start_time for t in raw_times]
	return relative_times, raw_num_inputs

def progressive_max(arr):
	return [max(arr[:i+1]) for i in range(len(arr))]

# assumes a file with the structure 
# data   afl_filename
# returns number of inputs generated -> max count
def parse_max_counts_afl(f):
	fname_re = re.compile(".*(queue|crashes|hangs)/id:(.*),(src|orig).*")
	queued = []
	crashes = []
	hangs = []
	for line in f:
		line = line.rstrip()
		split_line = line.split("\t")
		match = fname_re.match(split_line[1])
		if match == None:
			print("Error in parse_max_counts_afl: no match for filename:\n%s\n" % split_line[1])
			continue
		folder = match.group(1)
		if folder == "queue":
			ret_arr = queued
		elif folder == "crashes":
			ret_arr = crashes
		elif folder == "hangs":
			ret_arr = hangs
		id_num = int(match.group(2))
		data = int(split_line[0])
		if id_num < len(ret_arr):
			if (data != ret_arr[id_num]):
				print(line)
				print(id_num)
				print(ret_arr[id_num])
			ret_arr[id_num] = max(ret_arr[id_num], data)
			#assert(data == ret_arr[id_num])
		elif id_num == len(ret_arr):
			ret_arr.append(data)
		else:
			print("Error: out-of-order printing")
			return
	return progressive_max(queued), progressive_max(crashes), progressive_max(hangs)

#assumes a file with structure
# plot	timestamp
def parse_max_counts_slow(f):
	raw_times = []
	raw_max = []
	for line in f:
		line = line.rstrip()
		split_line = line.split('\t')
		raw_max.append(int(split_line[0]))
		raw_times.append(int(split_line[1]))
	start_time = min(raw_times)
	relative_times = [t - start_time for t in raw_times]
	return relative_times, raw_max

def max_at_m(arr1,arr2,arr3,t):
	m1,m2,m3 = t
	res1 = 0 if m1 == 0 else arr1[m1-1]
	res2 = 0 if m2 == 0 else arr2[m2-1]
	res3 = 0 if m3 == 0 else arr3[m3-1]
	return max(res1,res2,res3)	

def parse_afl(foldername):
	plot_data = open(foldername + "/plot_data")
	times, raw_num_inputs = parse_num_inputs_afl(plot_data)
	counts_data = open(foldername + "/counts-and-names")
	queued_counts, crashes_counts, hangs_counts = parse_max_counts_afl(counts_data)
	max_counts_per_gen = [max_at_m(queued_counts,crashes_counts,hangs_counts,m) for m in raw_num_inputs]
	return times, max_counts_per_gen

def parse_slow(foldername):
	f = open(foldername + "/counts-and-times")
	times, raw = parse_max_counts_slow(f)
	return times, progressive_max(raw)

def populate_counts(folder_prefixes, folder_suffixes):
	times = {}
	counts = {}
	n = len(folder_suffixes)
	for prefix in folder_prefixes:
		times[prefix] = [None] * n
		counts[prefix] = [None] * n
		for i in range(n):
			print("parsing %s-%d" % (prefix, i))
			suffix = folder_suffixes[i]
			if 'afl' in prefix:
				times[prefix][i], counts[prefix][i] = parse_afl(prefix + suffix)
			elif 'slow' in prefix:
				times[prefix][i], counts[prefix][i]= parse_slow(prefix + suffix)
			else:
				print("Not AFL or SLOW... I'm not sure what to do")
				return
	return times, counts




# def main():
if len (sys.argv) < 3:
	print("usage: python [-i] %s [numreps] [prefixes] [names]" % sys.argv[0])
	exit(1)
num_prefixes = int((len(sys.argv) -2 )/2)
for i in range(2, num_prefixes + 2):
	folder_prefixes.append(sys.argv[i])
print("Folder prefixes: " + str(folder_prefixes))
for i in range(num_prefixes + 2, 2*num_prefixes + 2):
	names.append(sys.argv[i])
print("names: " + str(names))
for i in range(0, int(sys.argv[1])):
	folder_suffixes.append("-" + str(i))
print("Folder suffixes: " + str(folder_suffixes))

all_times = set([])
times, counts = populate_counts(folder_prefixes, folder_suffixes)
for prefix in folder_prefixes:
	for suffix in range(len(folder_suffixes)):
		all_times = all_times.union(times[prefix][suffix])

# for folder_prefix in folder_prefixes:
# 	times[folder_prefix] = []
# 	percentages[folder_prefix] = []
# 	for folder_suffix in folder_suffixes:
# 		print "Parsing " + folder_prefix + folder_suffix + "/plot_data"
# 		file = open(folder_prefix + folder_suffix + "/plot_data")
# 		file_times, file_percentages = parse(file)
# 		all_times = all_times.union(set(file_times))
# 		times[folder_prefix].append(file_times)
# 		percentages[folder_prefix].append(file_percentages)
all_times_sorted = sorted(all_times)
for prefix in folder_prefixes:
	all_counts[prefix] = np.zeros((len(folder_suffixes),len(all_times_sorted)))
	for i in range(len(folder_suffixes)):
		print("processing " + prefix + folder_suffixes[i])
		all_counts[prefix][i] =  np.interp(all_times_sorted, times[prefix][i], counts[prefix][i])


all_times_hrs = [i / 3600.0 for i in all_times_sorted]
i = 0
plt.figure(figsize=(5,3.3))
for j in range(len(folder_prefixes)):
	prefix = folder_prefixes[j]
	name = names[j]
	means = np.mean(all_counts[prefix], axis = 0)
	plt.plot(all_times_hrs, means, linestyle=line_cycle[i], label=name, color=color_cycle[i])
	stds = np.std(all_counts[prefix], axis = 0)
	stds = stds/np.sqrt(len(all_counts[prefix]))
	stds = stds * CI_mult[len(all_counts[prefix])-2]
	plt.fill_between(all_times_hrs, means - stds, means + stds, facecolor=color_cycle[i], alpha=0.2)#,linestyle='dashed', edgecolor=color_cycle[i])
	i += 1

plt.legend(loc='best')
#plt.ylabel("Max Branches Exercised", fontdict={'size':'13'}, labelpad = 0.05)
#plt.xlabel("Time (hrs)")
#plt.subplots_adjust(left=0.18, bottom=0.17, right=0.98, top=0.99)
#bench_name = raw_input("benchmark name: ")
#print 'saving at: '+ '/home/eecs/clemieux/lfb-figs/24hr-runs/'+ bench_name+ '.png'
#plt.savefig('/home/eecs/clemieux/lfb-figs/24hr-runs/'+ bench_name+ '.png', format='png', dpi=1000)


# if __name__ == '__main__':
# 	main()
