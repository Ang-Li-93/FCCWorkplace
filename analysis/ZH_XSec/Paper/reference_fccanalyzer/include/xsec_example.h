#ifndef XSEC_EXAMPLE_H
#define XSEC_EXAMPLE_H

#include <cmath>
#include <vector>

#include "TLorentzVector.h"
#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"
#include "edm4hep/MCParticleData.h"
#include "edm4hep/ParticleIDData.h"

#include "ReconstructedParticle2MC.h"

namespace FCCAnalyses {
  


Vec_tlv makeLorentzVectors(Vec_rp in) {
	
	Vec_tlv result;
	for (auto & p: in) {
		TLorentzVector tlv;
		tlv.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
		result.push_back(tlv);
	}
	return result;
}

Vec_tlv makeLorentzVectors_gen(Vec_rp in, ROOT::VecOps::RVec<int> recind, ROOT::VecOps::RVec<int> mcind, ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> reco, ROOT::VecOps::RVec<edm4hep::MCParticleData> mc) {
	
	Vec_tlv result;
	for (auto & p: in) {
        
        int track_index = p.tracks_begin;
        int mc_index = ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        
		TLorentzVector tlv;
        if(mc_index >= 0 && mc_index < mc.size() ) {
            tlv.SetXYZM(mc.at(mc_index ).momentum.x, mc.at(mc_index).momentum.y, mc.at(mc_index).momentum.z, mc.at(mc_index).mass);
            result.push_back(tlv);
        }
        else {
            cout << "MC track not found!" << endl;
        }	
	}
	return result;
}




    
}

#endif
