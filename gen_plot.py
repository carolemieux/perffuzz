import sys
#import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

matplotlib.rcParams.update({'font.size':'14'})

CI_mult = [12.7062,4.3027,3.1824,2.7764,2.5706,2.4469,2.3646, 2.3060, 2.2622,2.2281,2.2010,2.1788,2.1604,2.1448, 2.131,2.120,2.110,2.101,2.093,2.086,2.080,2.074,2.069]

color_cycle=["#999999", "#E69F00", "#009E73",  "#0072B2"]
line_cycle=[":", "-.", "--", '-']

names = []
folder_prefixes = []
folder_suffixes = []
times = {}
percentages = {}
all_percentages = {}

def parse_num_inputs(f):
	raw_times = []
	raw_num_inputs = []
	for line in f:
		line = line.rstrip()
		if not line.startswith("#"):
			split_line = line.split(",")
			raw_times.append(int(split_line[0]))
			raw_num_inputs.append(int(split_line[3]))
	start_time = raw_times[0]
	relative_times = [t - start_time for t in raw_times]
	return relative_times, raw_num_inputs

# assumes a file with the structure 
# data   afl_filename
#
# or 
# data   mod_date
def parse_max_counts(f):


# def main():
if len (sys.argv) < 3:
	print "usage: python [-i] %s [numreps] [prefixes] [names]" % sys.argv[0]
num_prefixes = (len(sys.argv) -2 )/2
for i in range(2, num_prefixes + 2):
	folder_prefixes.append(sys.argv[i])
print "Folder prefixes: " + str(folder_prefixes)
for i in range(num_prefixes + 2, 2*num_prefixes + 2):
	names.append(sys.argv[i])
print "names: " + str(names)
for i in range(0, int(sys.argv[1])):
	folder_suffixes.append("-" + str(i))
print "Folder suffixes: " + str(folder_suffixes)
all_times = set([])
for folder_prefix in folder_prefixes:
	times[folder_prefix] = []
	percentages[folder_prefix] = []
	for folder_suffix in folder_suffixes:
		print "Parsing " + folder_prefix + folder_suffix + "/plot_data"
		file = open(folder_prefix + folder_suffix + "/plot_data")
		file_times, file_percentages = parse(file)
		all_times = all_times.union(set(file_times))
		times[folder_prefix].append(file_times)
		percentages[folder_prefix].append(file_percentages)
all_times_sorted = sorted(all_times)
for prefix in folder_prefixes:
	all_percentages[prefix] = np.zeros((len(folder_suffixes),len(all_times_sorted)))
	for i in range(len(folder_suffixes)):
		print "processing " + prefix + folder_suffixes[i] 
		all_percentages[prefix][i] =  np.interp(all_times_sorted, times[prefix][i], percentages[prefix][i])




all_times_hrs = [i / 3600.0 for i in all_times_sorted]
i = 0
plt.figure(figsize=(5,3.3))
for j in range(len(folder_prefixes)):
	prefix = folder_prefixes[j]
	name = names[j]
	means = np.mean(all_percentages[prefix], axis = 0)
	plt.plot(all_times_hrs, means, linestyle=line_cycle[i], label=name, color=color_cycle[i])
	stds = np.std(all_percentages[prefix], axis = 0)
	stds = stds/np.sqrt(len(all_percentages[prefix]))
	stds = stds * CI_mult[len(all_percentages[prefix])-2]
	plt.fill_between(all_times_hrs, means - stds, means + stds, facecolor=color_cycle[i], alpha=0.2)#,linestyle='dashed', edgecolor=color_cycle[i])
	i += 1

plt.legend(loc='best')
plt.ylabel("Basic Block Transitions Covered", fontdict={'size':'12'}, labelpad = 0.05)
plt.xlabel("Time (hrs)")
plt.subplots_adjust(left=0.18, bottom=0.17, right=0.98, top=0.99)
bench_name = raw_input("benchmark name: ")
print 'saving at: '+ '/home/eecs/clemieux/lfb-figs/24hr-runs/'+ bench_name+ '.png'
plt.savefig('/home/eecs/clemieux/lfb-figs/24hr-runs/'+ bench_name+ '.png', format='png', dpi=1000)


# if __name__ == '__main__':
# 	main()
