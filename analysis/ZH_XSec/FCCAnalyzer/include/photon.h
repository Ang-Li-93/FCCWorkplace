#ifndef ZH_PHOTON_H
#define ZH_PHOTON_H

#include <cmath>
#include <vector>

#include "TLorentzVector.h"
#include "ROOT/RVec.hxx"
#include "edm4hep/ReconstructedParticleData.h"
#include "edm4hep/MCParticleData.h"
#include "edm4hep/ParticleIDData.h"

#include "ReconstructedParticle2MC.h"

namespace FCCAnalyses {
    
struct resonanceHBuilder {
    
    float m_resonance_mass;
    resonanceHBuilder(float arg_resonance_mass);
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> operator()(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs) ;
};

resonanceHBuilder::resonanceHBuilder(float arg_resonance_mass) {m_resonance_mass = arg_resonance_mass;}

ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> resonanceHBuilder::resonanceHBuilder::operator()(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs)   {

    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    int n = legs.size();
    if(n >1) {
        ROOT::VecOps::RVec<bool> v(n);
        std::fill(v.end() - 2, v.end(), true);
        do {
            edm4hep::ReconstructedParticleData reso;
            TLorentzVector reso_lv; 
            for(int i = 0; i < n; ++i) {
                if (v[i]) {
                    TLorentzVector leg_lv;
                    leg_lv.SetXYZM(legs[i].momentum.x, legs[i].momentum.y, legs[i].momentum.z, legs[i].mass);
                    reso_lv += leg_lv;
                }
            }
            reso.momentum.x = reso_lv.Px();
            reso.momentum.y = reso_lv.Py();
            reso.momentum.z = reso_lv.Pz();
            reso.mass = reso_lv.M();
            result.emplace_back(reso);

        } while (std::next_permutation(v.begin(), v.end()));
    }
  
    if(result.size() > 1) {
        auto resonancesort = [&] (edm4hep::ReconstructedParticleData i ,edm4hep::ReconstructedParticleData j) { return (abs( m_resonance_mass -i.mass)<abs(m_resonance_mass-j.mass)); };
        std::sort(result.begin(), result.end(), resonancesort);
        ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>::const_iterator first = result.begin();
        ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>::const_iterator last = result.begin() + 1;
        ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> onlyBestReso(first, last);
        return onlyBestReso;
    } 
    else {
        return result;
    }
}


}


#endif
