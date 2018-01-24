/*
   american fuzzy lop - LLVM-mode instrumentation pass
   ---------------------------------------------------

   Written by Laszlo Szekeres <lszekeres@google.com> and
              Michal Zalewski <lcamtuf@google.com>

   LLVM integration design comes from Laszlo Szekeres. C bits copied-and-pasted
   from afl-as.c are Michal's fault.

   Copyright 2015, 2016 Google Inc. All rights reserved.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at:

     http://www.apache.org/licenses/LICENSE-2.0

   This library is plugged into LLVM when invoking clang through afl-clang-fast.
   It tells the compiler to add code roughly equivalent to the bits discussed
   in ../afl-as.h.

 */

#define AFL_LLVM_PASS

#include "../config.h"
#include "../debug.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <iostream>
#include <fstream>

#include "llvm/ADT/Statistic.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/Debug.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/IR/DebugInfo.h"

using namespace llvm;

namespace {

  class AFLCoverage : public ModulePass {

    public:

      static char ID;
      AFLCoverage() : ModulePass(ID) { }

      bool runOnModule(Module &M) override;

      // StringRef getPassName() const override {
      //  return "American Fuzzy Lop Instrumentation";
      // }

  };

}


char AFLCoverage::ID = 0;

static inline void dump_loc(std::ostream& out, const char* name, const DebugLoc& dd) {
  if (std::getenv("DUMP_INFO") == NULL) { return; }
  if(!dd) { return; }
  auto* scope = cast<DIScope>(dd.getScope());
  out << ", \"" << name << "\": { \"file\": \"" << scope->getFilename().str()
      << "\", \"line\": " << dd.getLine()
      << ", \"column\": " << dd.getCol() << " }";
}


static inline void dump_branch(std::ostream& out, const BasicBlock& bb, const unsigned int cur_loc) {
  if (std::getenv("DUMP_INFO") == NULL) { return; }
  out << "{ \"type\": \"bb\", ";
  out << "\"id\": " << cur_loc;
  dump_loc(out, "begin", bb.getInstList().begin()->getDebugLoc());
  dump_loc(out, "end", bb.getTerminator()->getDebugLoc());
  out << "}" << std::endl;
}

static inline std::string loc_description (const DebugLoc& dd) {
  if(!dd) { return ""; }
  auto* scope = cast<DIScope>(dd.getScope());
  return scope->getFilename().str() + ":" + std::to_string(dd.getLine()) + ":" + std::to_string(dd.getCol()); 
}

static inline std::string bb_description(const BasicBlock& bb) {
  return "(" + loc_description(bb.getInstList().begin()->getDebugLoc()) + "-" + loc_description(bb.getTerminator()->getDebugLoc()) + ")";

}

static inline std::string edge_descp(std::map<unsigned int, std::vector<std::string>> descp_map , const unsigned int pred_id, const unsigned int suc_id){
  std::string ret_string = "";
  unsigned int edge_id = (pred_id >> 1) ^ suc_id;
  std::vector<std::string> pred_descps = descp_map[pred_id];
  std::vector<std::string> suc_descps = descp_map[suc_id];
  for (auto &pred_descp : pred_descps) {
    for (auto &suc_descp : suc_descps) {
      ret_string += std::to_string(edge_id) + pred_descp + "->" + suc_descp + "\n";
    }
  }
  return ret_string;
}

static inline void dump_edge_descp(std::ostream& out, std::map<unsigned int, std::vector<std::string>> descp_map, const unsigned int pred_id, const unsigned int suc_id) {
   out << edge_descp(descp_map, pred_id, suc_id);
}

static inline void dump_edge(std::ostream& out, const unsigned int pred_id, const unsigned int suc_id) { 
  if (std::getenv("DUMP_INFO") == NULL) { return; }
  out << "{ \"type\": \"edge\", \"pred_id\": " << pred_id << ", \"suc_id\": " << suc_id << " }" << std::endl;
}

bool AFLCoverage::runOnModule(Module &M) {

  LLVMContext &C = M.getContext();

  IntegerType *Int8Ty  = IntegerType::getInt8Ty(C);
  IntegerType *Int32Ty = IntegerType::getInt32Ty(C);

  /* Show a banner */

  char be_quiet = 0;

  if (isatty(2) && !getenv("AFL_QUIET")) {

    SAYF(cCYA "afl-llvm-pass " cBRI VERSION cRST " by <lszekeres@google.com>\n");

  } else be_quiet = 1;

  /* Decide instrumentation ratio */

  char* inst_ratio_str = getenv("AFL_INST_RATIO");
  unsigned int inst_ratio = 100;

  if (inst_ratio_str) {

    if (sscanf(inst_ratio_str, "%u", &inst_ratio) != 1 || !inst_ratio ||
        inst_ratio > 100)
      FATAL("Bad value of AFL_INST_RATIO (must be between 1 and 100)");

  }

  std::ofstream branch_info("branch.info", std::ofstream::app);

  /* Get globals for the SHM region and the previous location. Note that
     __afl_prev_loc is thread-local. */

  GlobalVariable *AFLMapPtr =
      new GlobalVariable(M, PointerType::get(Int8Ty, 0), false,
                         GlobalValue::ExternalLinkage, 0, "__afl_area_ptr");
  
  GlobalVariable *AFLPerfPtr =
      new GlobalVariable(M, PointerType::get(Int32Ty, 0), false,
                         GlobalValue::ExternalLinkage, 0, "__afl_perf_ptr");

  GlobalVariable *AFLPrevLoc = new GlobalVariable(
      M, Int32Ty, false, GlobalValue::ExternalLinkage, 0, "__afl_prev_loc",
      0, GlobalVariable::GeneralDynamicTLSModel, 0, false);

  ConstantInt* PerfMask = ConstantInt::get(Int32Ty, PERF_SIZE-1);

  /* Instrument all the things! */

  int inst_blocks = 0;
  DenseMap<const BasicBlock*, unsigned int> afl_bb_ids;
  std::map<unsigned int, std::vector<std::string>> ids_to_descp;

  for (auto &F : M)
    for (auto &BB : F) {

      BasicBlock::iterator IP = BB.getFirstInsertionPt();
      IRBuilder<> IRB(&(*IP));

      if (AFL_R(100) >= inst_ratio) continue;

      /* Make up cur_loc */

      unsigned int cur_loc = AFL_R(MAP_SIZE);
      const BasicBlock* bb_ptr = &BB;
     
      afl_bb_ids.insert(std::make_pair(bb_ptr, cur_loc));
      //dump_branch(branch_info, BB, cur_loc);
      
      if (ids_to_descp.find(cur_loc) == ids_to_descp.end()) {
        ids_to_descp[cur_loc] = std::vector<std::string>();
      }
      ids_to_descp[cur_loc].push_back(bb_description(BB));
     
      ConstantInt *CurLoc = ConstantInt::get(Int32Ty, cur_loc);

      /* Load prev_loc */

      LoadInst *PrevLoc = IRB.CreateLoad(AFLPrevLoc);
      PrevLoc->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));
      Value *PrevLocCasted = IRB.CreateZExt(PrevLoc, IRB.getInt32Ty());

      /* Get edge ID as XOR */
      Value* EdgeId = IRB.CreateXor(PrevLocCasted, CurLoc);

      /* Load SHM pointer */

      LoadInst *MapPtr = IRB.CreateLoad(AFLMapPtr);
      MapPtr->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));
      Value *MapPtrIdx =
          IRB.CreateGEP(MapPtr, EdgeId);
      
      LoadInst *PerfPtr = IRB.CreateLoad(AFLPerfPtr);
      PerfPtr->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));
      Value *PerfBranchPtr =
          IRB.CreateGEP(PerfPtr, IRB.CreateAnd(EdgeId, PerfMask));

      /* Update bitmap */

      LoadInst *Counter = IRB.CreateLoad(MapPtrIdx);
      Counter->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));
      Value *Incr = IRB.CreateAdd(Counter, ConstantInt::get(Int8Ty, 1));
      IRB.CreateStore(Incr, MapPtrIdx)
          ->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));
      
      /* Increment performance counter for branch */
      LoadInst *PerfBranchCounter = IRB.CreateLoad(PerfBranchPtr);
      PerfBranchCounter->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));
      Value *PerfBranchIncr = IRB.CreateAdd(PerfBranchCounter, ConstantInt::get(Int32Ty, 1));
      IRB.CreateStore(PerfBranchIncr, PerfBranchPtr)
          ->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));
      
      /* Increment performance counter for total count  */
      LoadInst *PerfTotalCounter = IRB.CreateLoad(PerfPtr); // Index 0 of the perf map
      PerfTotalCounter->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));
      Value *PerfTotalIncr = IRB.CreateAdd(PerfTotalCounter, ConstantInt::get(Int32Ty, 1));
      IRB.CreateStore(PerfTotalIncr, PerfPtr)
          ->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));

      /* Set prev_loc to cur_loc >> 1 */

      StoreInst *Store =
          IRB.CreateStore(ConstantInt::get(Int32Ty, cur_loc >> 1), AFLPrevLoc);
      Store->setMetadata(M.getMDKindID("nosanitize"), MDNode::get(C, None));

      inst_blocks++;

    }

  // dump cfg edges
  for (auto &F : M) {
    for (auto &BB : F) {
        BasicBlock& bb = BB;
        const BasicBlock* bb_ptr = &BB;
        auto pred_id = afl_bb_ids.lookup(bb_ptr);
        TerminatorInst* term = bb.getTerminator();
        for(BasicBlock* suc : term->successors()) {
          auto suc_id = afl_bb_ids.lookup(suc);
          //dump_edge(branch_info, pred_id, suc_id);
          dump_edge_descp(branch_info, ids_to_descp, pred_id, suc_id);
        }
    }
  }
  branch_info.close();

  /* Say something nice. */

  if (!be_quiet) {

    if (!inst_blocks) WARNF("No instrumentation targets found.");
    else OKF("Instrumented %u locations (%s mode, ratio %u%%).",
             inst_blocks, getenv("AFL_HARDEN") ? "hardened" :
             ((getenv("AFL_USE_ASAN") || getenv("AFL_USE_MSAN")) ?
              "ASAN/MSAN" : "non-hardened"), inst_ratio);

  }

  return true;

}


static void registerAFLPass(const PassManagerBuilder &,
                            legacy::PassManagerBase &PM) {

  PM.add(new AFLCoverage());

}


static RegisterStandardPasses RegisterAFLPass(
    PassManagerBuilder::EP_OptimizerLast, registerAFLPass);

static RegisterStandardPasses RegisterAFLPass0(
    PassManagerBuilder::EP_EnabledOnOptLevel0, registerAFLPass);
