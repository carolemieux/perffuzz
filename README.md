

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


 ## Running PerfFuzz on a program of your choice
 
 ### Compile your program with perffuzz
 
 To compile your C/C++ program with perffuzz, replace ```CC``` (resp. ```CXX```) with ```path/to/perffuzz/afl-clang-fast``` (resp. ```path/to/perffuzz/afl-clang-fast++```) in your build process. 
 See section (3) of README (not README.md) for more details, replacing references of ```path/to/afl/afl-gcc``` with ```path/to/perffuzz/afl-clang-fast```.
 
-  Q: ```afl-clang-fast``` doesn't exist!
-  A: make sure you ran ```make``` in the ```llvm_mode``` directory (see "Building PerfFuzz")
 

### Run PerfFuzz on your program.

 In short, follow the instructions in README (regular AFL readme) section 6, but add the ```-p``` option to enable PerfFuzz, and the ```-N num``` option to restrict the size of produced inputs to a maximum file size of ```num```. Make sure your initial seed inputs (in the input directory) are of smaller size than ```num``` bytes!
 
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
