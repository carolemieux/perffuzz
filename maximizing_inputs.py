#!/usr/bin/env pypy
"""
 Copyright (c) 2017, University of California, Berkeley

 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are
 met:

 1. Redistributions of source code must retain the above copyright
 notice, this list of conditions and the following disclaimer.

 2. Redistributions in binary form must reproduce the above copyright
 notice, this list of conditions and the following disclaimer in the
 documentation and/or other materials provided with the distribution.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import argparse
from collections import defaultdict
import re
import sys

# Global constants
REGEXP_BRANCH = re.compile("^BRANCH (.*)$")
REGEXP_END = re.compile("^# End (.*)$")

def main():    
    trace_file_name = sys.argv[1]

    # Create new analysis object
    analysis = TraceAnalysis()

    # Process trace file
    analysis.process_trace(trace_file_name)

    # Print inputs and maximizing branches
    maximizing_inputs = analysis.get_maximizing_inputs()
    sorted_counts = sorted(maximizing_inputs.items(), key=lambda p: p[1][1], reverse=True)
    for loc, (input, count) in sorted_counts:
        print count, loc, input


class TraceAnalysis(object):

    def process_trace(self, trace_file_name):
        self.branch_counts = defaultdict(int) # INT x INT -> INT // Map of (IID, Arm) to counts for this input
        self.inputs_to_branch_counts = {}     # STR -> ((INT x INT) -> INT) // Map of inputs to branch counts
        with open(trace_file_name) as trace_file:
            while True:
                # Read line from file
                line = trace_file.readline()
                # End-of-file is empty line
                if not line:
                    break

                # Try to match BRANCH(iid, arm, line)
                match_branch = REGEXP_BRANCH.match(line)
                if match_branch:
                    self.handle_branch(match_branch.group(1))
                    continue

                # Try to match end-of-input
                match_end = REGEXP_END.match(line)
                if match_end:
                    self.handle_end(match_end.group(1))
                    continue



                # Otherwise, error
                raise Exception("Cannot parse trace line: " + line)


    def handle_branch(self, loc):
        # Increment branch count
        self.branch_counts[loc] += 1

    def handle_end(self, input):
        # Save current counts to map
        self.inputs_to_branch_counts[input] = self.branch_counts
        # Reset branch counts
        self.branch_counts = defaultdict(int)

    def get_maximizing_inputs(self):
        max_branch_counts = defaultdict(int)
        maximizing_inputs = {}
        for input, branch_counts in self.inputs_to_branch_counts.iteritems():
            for branch, count in branch_counts.iteritems():
                if count > max_branch_counts[branch]:
                    max_branch_counts[branch] = count
                    maximizing_inputs[branch] = (input, count)

        return maximizing_inputs



if __name__ == "__main__":
    main()








