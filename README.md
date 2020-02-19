

#  PerfFuzz

<img align="left" src="perffuzz-logo.png" width=100>
Performance problems in software can arise unexpectedly when programs are provided with inputs that exhibit pathological behavior. But how can we find these inputs in the first place? PerfFuzz can generate such inputs automatically: given a program and at least one seed input, PerfFuzz automatically generates inputs that exercise pathological behavior across program locations, without any domain knowledge. 

PerfFuzz uses multi-dimensional performance feedback and independently maximizes execution counts for all program locations. This enables PerfFuzz to find a variety of inputs that exercise distinct hot spots in a program.

Read the [ISSTA paper](http://www.carolemieux.com/perffuzz-issta2018.pdf) for more details.


Built by Caroline Lemieux (clemieux@cs.berkeley.edu) and Rohan Padhye (rohanpadhye@cs.berkeley.edu) on top of Michal Zalewski's  (lcamtuf@google.com) AFL.

## Building PerfFuzz

To build on *nix machines, run

```
make
```
 
 in the ```perffuzz``` directory. Since PerfFuzz is built on AFL, it will not build on Windows machines. You will also need to build PerfFuzz's instrumenting compiler, which can be done by running
 
 ```
 cd llvm_mode
 make
 cd ..
 ```
 in the ```perffuzz``` directory, after having built PerfFuzz.
 
 
-  Q: What version of clang should I use?
-  A: PerfFuzz was evaluated with clang-3.8.0 on Linux and works with verison 8 on Mac. To experiment with different clang/LLVM version, add the bin/ directory from the pre-build clang archives to the front of your PATH when compiling. 

-  Q: I'm getting an error involving the ```-fno-rtti``` option.
-  A: If you're on Redhat Linux, this may be a gcc/clang [compatibility issue](https://www.google.com/search?rlz=1C5CHFA_enUS731US732&ei=2u76W-eWLcSC_wT4g5vYBw&q=redhat+no+rtti+typeid&oq=redhat+no+rtti+typeid). Apparently [gcc-4.7 fixes the issue](https://issues.couchbase.com/browse/JSCBC-307). 

## Test PerfFuzz on Insertion Sort

To check whether PerfFuzz is working correctly, try running it on the insertion sort benchmark provided. The following commands assume you are in the  PerfFuzz directory. 

### Build

First, compile the benchmark:
```
./afl-clang-fast insertion-sort.c -o isort
```

### Run PerfFuzz
Let's make some seeds for PerfFuzz to start with:

```
mkdir isort-seeds
head -c 64 /dev/zero > isort-seeds/zeroes
```

Now we can run PerfFuzz:
```
./afl-fuzz -p -i isort-seeds -o isort_perf_test/ -N 64 ./isort @@
```
You should see the number of `total paths` (this is a misnomer; it's just the number of saved inputs) increase consistently. You can also check to see if the saved inputs are heading towards a worst-case by running
```
for i in isort_perf_test/queue/id*; do ./isort $i | grep comps; done
```
(which, for each saved input, plots the number of comparisons insertion sort performed while sorting that input) 

For comparison with the performance compared to regular afl, you can run:
```./afl-fuzz -i isort-seeds -o isort_afl_test/ -N 64 ./isort @@```
without the `-p` option, this should just run regular AFL. You should see `total_paths` quickly topping out around ~20 or so, and the number of cycles increase a lot. There will probably be much fewer comparisons performed for the saved inputs as well. The highest number of comparisons printed when you run:
```
for i in isort_afl_test/queue/id*; do ./isort $i | grep comps; done
```
should be smaller than what you saw for the inputs in `isort_perf_test/queue`.

 ## Running PerfFuzz on a program of your choice
 
 ### Compile your program with PerfFuzz
 
 To compile your C/C++ program with perffuzz, replace ```CC``` (resp. ```CXX```) with ```path/to/perffuzz/afl-clang-fast``` (resp. ```path/to/perffuzz/afl-clang-fast++```) in your build process. 
 See section (3) of README (not README.md) for more details, replacing references of ```path/to/afl/afl-gcc``` with ```path/to/perffuzz/afl-clang-fast```.
 
-  Q: ```afl-clang-fast``` doesn't exist!
-  A: make sure you ran ```make``` in the ```llvm_mode``` directory (see "Building PerfFuzz")
 

### Run PerfFuzz on your program.

 In short, follow the instructions in README (regular AFL readme) section 6, but __add the ```-p``` option to enable PerfFuzz__, and the ```-N num``` option to restrict the size of produced inputs to a maximum file size of ```num```. Make sure your initial seed inputs (in the input directory) are of smaller size than ```num``` bytes!
 
 On many programs (including the benchmarks in the paper), the ```-d``` option ([Fidgety](https://groups.google.com/forum/#!topic/afl-users/1PmKJC-EKZ0) mode) offers better performance. 
 
 Let PerfFuzz run for as long as you like: we ran for a few hours on larger benchmarks.
 
 ### Interpret PerfFuzz results.
 
In the ```queue``` directory of the ouput directory, inputs postfixed with ```+max``` were saved because the maximized a performance key. 
 
We provide some tools to help analyze the results. Notably, ```afl-showmax``` can print:
1. The total path length (default)
2. The maximum hotspot (```-x``` option)
3. The entire performance map in a key:value format (```-a``` option)

To build ```afl-showmax```, run
```
make afl-showmax
```
in the PerfFuzz directory. 
