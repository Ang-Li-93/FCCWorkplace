#ifndef FCCANALYZER_UTILS_H
#define FCCANALYZER_UTILS_H

#include "defines.h"

namespace FCCAnalyses {
    
// maps theta [pi/2, pi] to [0, pi/2]
Vec_f theta_abs(Vec_f in) {
    
    Vec_f result;
    result.reserve(in.size());
    
    for(int i = 0; i < in.size(); ++i) {
        
        if(in[i] > M_PI/2.0) result.push_back(M_PI/2.0-in[i]);
        else result.push_back(in[i]);
    }
    return result;
}

// deltaR between two reco particles, based on eta
float deltaR(Vec_rp in) {
    if(in.size() != 2) return -1;
    
    ROOT::Math::PxPyPzEVector tlv1;
    tlv1.SetPxPyPzE(in.at(0).momentum.x, in.at(0).momentum.y, in.at(0).momentum.z, in.at(0).energy);

    ROOT::Math::PxPyPzEVector tlv2;
    tlv2.SetPxPyPzE(in.at(1).momentum.x, in.at(1).momentum.y, in.at(1).momentum.z, in.at(1).energy);
    
    return std::sqrt(std::pow(tlv1.Eta()-tlv2.Eta(), 2) + std::pow(tlv1.Phi()-tlv2.Phi(), 2));
}

//// acolinearity between two reco particles
//float acolinearity(Vec_rp in) {
//    if(in.size() != 2) return -1;
//
//    TLorentzVector p1;
//    p1.SetXYZM(in[0].momentum.x, in[0].momentum.y, in[0].momentum.z, in[0].mass);
//
//    TLorentzVector p2;
//    p2.SetXYZM(in[1].momentum.x, in[1].momentum.y, in[1].momentum.z, in[1].mass);
//
//    float acol = abs(p1.Theta() - p2.Theta());
//    return acol;
//}
//
//// acoplanarity between two reco particles
//float acoplanarity(Vec_rp in) {
//    if(in.size() != 2) return -1;
//
//    TLorentzVector p1;
//    p1.SetXYZM(in[0].momentum.x, in[0].momentum.y, in[0].momentum.z, in[0].mass);
//
//    TLorentzVector p2;
//    p2.SetXYZM(in[1].momentum.x, in[1].momentum.y, in[1].momentum.z, in[1].mass);
//
//    float acop = abs(p1.Phi() - p2.Phi());
//    if(acop > M_PI) acop = 2 * M_PI - acop;
//    acop = M_PI - acop;
//
//    return acop;
//}

// visible energy
float visibleEnergy(Vec_rp in, float p_cutoff = 0.0) {
    float e = 0;
    for(auto &p : in) {
        if (std::sqrt(p.momentum.x * p.momentum.x + p.momentum.y*p.momentum.y) < p_cutoff) continue;
        e += p.energy;
    }
    return e;
}

// returns missing energy vector, based on reco particles
Vec_rp missingEnergy(float ecm, Vec_rp in, float p_cutoff = 0.0) {
    float px = 0, py = 0, pz = 0, e = 0;
    for(auto &p : in) {
        if (std::sqrt(p.momentum.x * p.momentum.x + p.momentum.y*p.momentum.y) < p_cutoff) continue;
        px += -p.momentum.x;
        py += -p.momentum.y;
        pz += -p.momentum.z;
        e += p.energy;
    }
    
    Vec_rp ret;
    rp res;
    res.momentum.x = px;
    res.momentum.y = py;
    res.momentum.z = pz;
    res.energy = ecm-e;
    ret.emplace_back(res);
    return ret;
    
}

// calculate the visisble mass of the event
float visibleMass(Vec_rp in, float p_cutoff = 0.0) {
    float px = 0, py = 0, pz = 0, e = 0;
    for(auto &p : in) {
        if (std::sqrt(p.momentum.x * p.momentum.x + p.momentum.y*p.momentum.y) < p_cutoff) continue;
        px += p.momentum.x;
        py += p.momentum.y;
        pz += p.momentum.z;
        e += p.energy;
    }

    float ptot2 = std::pow(px, 2) + std::pow(py, 2) + std::pow(pz, 2);
    float de2 = std::pow(e, 2);
    if (de2 < ptot2) return -999.;
    float Mvis = std::sqrt(de2 - ptot2);
    return Mvis;
}
  
// calculate the missing mass, given a ECM value
float missingMass(float ecm, Vec_rp in, float p_cutoff = 0.0) {
    float px = 0, py = 0, pz = 0, e = 0;
    for(auto &p : in) {
        if (std::sqrt(p.momentum.x * p.momentum.x + p.momentum.y*p.momentum.y) < p_cutoff) continue;
        px += p.momentum.x;
        py += p.momentum.y;
        pz += p.momentum.z;
        e += p.energy;
    }
    if(ecm < e) return -99.;

    float ptot2 = std::pow(px, 2) + std::pow(py, 2) + std::pow(pz, 2);
    float de2 = std::pow(ecm - e, 2);
    if (de2 < ptot2) return -999.;
    float Mmiss = std::sqrt(de2 - ptot2);
    return Mmiss;
}
    




   





ROOT::VecOps::RVec<float> leptonResolution_p(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> muons, ROOT::VecOps::RVec<int> recind,
                                ROOT::VecOps::RVec<int> mcind,
                                ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> reco,
                                ROOT::VecOps::RVec<edm4hep::MCParticleData> mc){
    
    ROOT::VecOps::RVec<float> result;
    result.reserve(muons.size());
    
    for(int i = 0; i < muons.size(); ++i) {

        TLorentzVector reco_;
        reco_.SetXYZM(muons[i].momentum.x, muons[i].momentum.y, muons[i].momentum.z, muons[i].mass);
        int track_index = muons[i].tracks_begin;
        int mc_index = FCCAnalyses::ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        if(mc_index >= 0 && mc_index < (int)mc.size()) {
            TLorentzVector mc_;
            mc_.SetXYZM(mc.at(mc_index).momentum.x, mc.at(mc_index).momentum.y, mc.at(mc_index).momentum.z, mc.at(mc_index).mass);
            result.push_back(reco_.P()/mc_.P());
            //if(mc_.P() > 20) result.push_back(reco_.P()/mc_.P());
		}
    } 
    return result;
}



struct resonanceBuilder {
    float m_resonance_mass;
    resonanceBuilder(float arg_resonance_mass);
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> operator()(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs);
};  

resonanceBuilder::resonanceBuilder(float arg_resonance_mass) { m_resonance_mass = arg_resonance_mass; }
ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> resonanceBuilder::operator()(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs) {
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    int n = legs.size();
    if(n >1) {
        ROOT::VecOps::RVec<bool> v(n);
        std::fill(v.end() - 2, v.end(), true);
        do {
            edm4hep::ReconstructedParticleData reso;
            TLorentzVector reso_lv;
            for(int i = 0; i < n; ++i) {
                if(v[i]) {
                    reso.charge += legs[i].charge;
                    TLorentzVector leg_lv;
                    leg_lv.SetXYZM(legs[i].momentum.x, legs[i].momentum.y, legs[i].momentum.z, legs[i].mass);
                    reso_lv += leg_lv;
                }
            }
            if(reso.charge != 0) continue;
            reso.momentum.x = reso_lv.Px();
            reso.momentum.y = reso_lv.Py();
            reso.momentum.z = reso_lv.Pz();
            reso.mass = reso_lv.M();
            result.emplace_back(reso);
        } 
        while(std::next_permutation(v.begin(), v.end()));
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














// compute the cone isolation for reco particles
struct coneIsolation {

    coneIsolation(float arg_dr_min, float arg_dr_max);
    double deltaR(double eta1, double phi1, double eta2, double phi2) { return TMath::Sqrt(TMath::Power(eta1-eta2, 2) + (TMath::Power(phi1-phi2, 2))); };

    float dr_min = 0;
    float dr_max = 0.4;
    Vec_f operator() (Vec_rp in, Vec_rp rps) ;
};

coneIsolation::coneIsolation(float arg_dr_min, float arg_dr_max) : dr_min(arg_dr_min), dr_max( arg_dr_max ) { };
Vec_f coneIsolation::coneIsolation::operator() (Vec_rp in, Vec_rp rps) {
  
    Vec_f result;
    result.reserve(in.size());

    std::vector<ROOT::Math::PxPyPzEVector> lv_reco;
    std::vector<ROOT::Math::PxPyPzEVector> lv_charged;
    std::vector<ROOT::Math::PxPyPzEVector> lv_neutral;

    for(size_t i = 0; i < rps.size(); ++i) {

        ROOT::Math::PxPyPzEVector tlv;
        tlv.SetPxPyPzE(rps.at(i).momentum.x, rps.at(i).momentum.y, rps.at(i).momentum.z, rps.at(i).energy);
        
        if(rps.at(i).charge == 0) lv_neutral.push_back(tlv);
        else lv_charged.push_back(tlv);
    }
    
    for(size_t i = 0; i < in.size(); ++i) {

        ROOT::Math::PxPyPzEVector tlv;
        tlv.SetPxPyPzE(in.at(i).momentum.x, in.at(i).momentum.y, in.at(i).momentum.z, in.at(i).energy);
        lv_reco.push_back(tlv);
    }

    
    // compute the isolation (see https://github.com/delphes/delphes/blob/master/modules/Isolation.cc#L154) 
    for (auto & lv_reco_ : lv_reco) {
    
        double sumNeutral = 0.0;
        double sumCharged = 0.0;
    
        // charged
        for (auto & lv_charged_ : lv_charged) {
    
            double dr = coneIsolation::deltaR(lv_reco_.Eta(), lv_reco_.Phi(), lv_charged_.Eta(), lv_charged_.Phi());
            if(dr > dr_min && dr < dr_max) sumCharged += lv_charged_.P();
        }
        
        // neutral
        for (auto & lv_neutral_ : lv_neutral) {
    
            double dr = coneIsolation::deltaR(lv_reco_.Eta(), lv_reco_.Phi(), lv_neutral_.Eta(), lv_neutral_.Phi());
            if(dr > dr_min && dr < dr_max) sumNeutral += lv_neutral_.P();
        }
        
        double sum = sumCharged + sumNeutral;
        double ratio= sum / lv_reco_.P();
        result.emplace_back(ratio);
    }
    return result;
}


// filter reconstructed particles (in) based a property (prop) within a defined range (m_min, m_max)
struct sel_range {
    sel_range(float arg_min, float arg_max, bool arg_abs = false);
    float m_min = 0.;
    float m_max = 1.;
    bool m_abs = false;
    Vec_rp operator() (Vec_rp in, Vec_f prop);
};

sel_range::sel_range(float arg_min, float arg_max, bool arg_abs) : m_min(arg_min), m_max(arg_max), m_abs(arg_abs) {};
Vec_rp sel_range::operator() (Vec_rp in, Vec_f prop) {
    Vec_rp result;
    result.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
        auto & p = in[i];
        float val = (m_abs) ? abs(prop[i]) : prop[i];
        if(val > m_min && val < m_max) result.emplace_back(p);
    }
    return result;
}









// obsolete
struct sel_iso {
    sel_iso(float arg_max_iso);
    float m_max_iso = .25;
    Vec_rp operator() (Vec_rp in, Vec_f iso);
  };

sel_iso::sel_iso(float arg_max_iso) : m_max_iso(arg_max_iso) {};
ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>  sel_iso::operator() (Vec_rp in, Vec_f iso) {
    Vec_rp result;
    result.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
        auto & p = in[i];
        if (iso[i] < m_max_iso) {
            result.emplace_back(p);
        }
    }
    return result;
}


// obsolete
struct sel_eta {
    sel_eta(float arg_min_eta, float arg_max_eta = 1e10, bool arg_abs = true);
    float m_min_eta = 1.;
    float m_max_eta = 1e10;
    bool m_abs = true;
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>  operator() (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in);
};


sel_eta::sel_eta(float arg_min_eta, float arg_max_eta, bool arg_abs) : m_min_eta(arg_min_eta), m_max_eta(arg_max_eta), m_abs(arg_abs)  {};
ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>  sel_eta::operator() (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in) {
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    result.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
        auto & p = in[i];
        TLorentzVector tlv;
        tlv.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        float eta = (m_abs) ? abs(tlv.Eta()) : tlv.Eta();
        if(eta > m_min_eta && eta < m_max_eta) result.emplace_back(p);
    }
    return result;
}




}



#endif
