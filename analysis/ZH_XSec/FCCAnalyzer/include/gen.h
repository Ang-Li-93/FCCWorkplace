#ifndef FCCANALYZER_GEN_H
#define FCCANALYZER_GEN_H

#include "defines.h"

namespace FCCAnalyses {
    

Vec_mc get_gen_pdg(Vec_mc mc, int pdgId, bool abs= true) {

   Vec_mc result;
   for(size_t i = 0; i < mc.size(); ++i) {
       
        auto & p = mc[i];
        if((abs and std::abs(p.PDG) == pdgId) or (not abs and p.PDG == pdgId)) result.emplace_back(p);
   }
   return result;
}

}

#endif
