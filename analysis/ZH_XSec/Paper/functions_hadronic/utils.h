

namespace FCCAnalyses {


bool is_ww_leptonic(Vec_mc mc, Vec_i ind) {
   int l1 = 0;
   int l2 = 0;
   //cout << "*********" << endl;
   for(size_t i = 0; i < mc.size(); ++i) {
        auto & p = mc[i];
        if(std::abs(p.PDG) == 24) {
            int ds = p.daughters_begin;
            int de = p.daughters_end;
            for(int k=ds; k<de; k++) {
                int pdg = abs(mc[ind[k]].PDG);
                if(pdg == 24) continue;
                //std::cout << "W " << pdg << endl;
                if(pdg == 11 or pdg == 13) {
                    if(l1 == 0) l1 = pdg;
                    else l2 = pdg;
                }
            }
        }
        else if(std::abs(p.PDG) == 15) { // tau decays
            int ds = p.daughters_begin;
            int de = p.daughters_end;
            for(int k=ds; k<de; k++) {
                int pdg = abs(mc[ind[k]].PDG);
                if(pdg == 15) continue;
                //std::cout << "T " << pdg << endl;
                if(pdg == 11 or pdg == 13) {
                    if(l1 == 0) l1 = pdg;
                    else l2 = pdg;
                }
            }
        }
   }
   if(l1 == l2 && (l1==13 || l1 == 11)) {
       //std::cout << "LEPTONIC-----------" << l1 << " " << l2 << endl;
       return true;
   }
   return false;
}



bool is_hzz_invisible(Vec_mc mc, Vec_i ind) {
   bool is_inv = true;
   int d1 = 0;
   int d2 = 0;
   for(size_t i = 0; i < mc.size(); ++i) {
        auto & p = mc[i];
        if(std::abs(p.PDG) != 23) continue;

        int ds = p.daughters_begin;
        int de = p.daughters_end;
        int idx_ds = ind[ds];
        int idx_de = ind[de-1];
        int pdg_d1 = abs(mc[idx_ds].PDG);
        int pdg_d2 = abs(mc[idx_de].PDG);

        if(std::abs(pdg_d1) == 23 or std::abs(pdg_d2) == 23) continue;
        if(d1 == 0) d1  += pdg_d1 + pdg_d2;
        else d2  += pdg_d1 + pdg_d2;
   }
   if((d1==24 || d1==28 || d1==32) && (d2==24 || d2==28 || d2==32)) {
       return true;
   }
   return false;
}



Vec_i ww_decay_mode(Vec_mc mc, Vec_i ind) {
   Vec_i res; // returns vector of 4 indices (first two PDG of W+ daughters, second two PDG of W-)
   res.push_back(-99);
   res.push_back(-99);
   res.push_back(-99);
   res.push_back(-99);
   for(size_t i = 0; i < mc.size(); ++i) {
        auto & p = mc[i];
        if(std::abs(p.PDG) != 24) continue;

        int ds = p.daughters_begin;
        int de = p.daughters_end;
        int idx_ds = ind[ds];
        int idx_de = ind[de-1];
        int pdg_d1 = mc[idx_ds].PDG;
        int pdg_d2 = mc[idx_de].PDG;

        if(std::abs(pdg_d1) == 24 or std::abs(pdg_d2) == 24) continue;
        if(p.PDG == 24) {
            res[0] = pdg_d1;
            res[1] = pdg_d2;
        }
        else {
            res[2] = pdg_d1;
            res[3] = pdg_d2;
        }
   }
   return res;
}



Vec_mc get_photons(Vec_mc mc) {

   Vec_mc result;
   for(size_t i = 0; i < mc.size(); ++i) {
        auto & p = mc[i];
        if(p.PDG == 22) result.emplace_back(p);
   }
   return result;
}

// get the gen p from reco
Vec_f gen_p_from_reco(Vec_rp legs, Vec_i recind, Vec_i mcind, Vec_rp reco, Vec_mc mc) {

   Vec_f result;
   for (size_t i = 0; i < legs.size(); ++i) {
        int track_index = legs[i].tracks_begin;
        int mc_index = ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        
        TLorentzVector leg_lv;
        if(mc_index >= 0 && mc_index < mc.size() ) {
            leg_lv.SetXYZM(mc.at(mc_index ).momentum.x, mc.at(mc_index ).momentum.y, mc.at(mc_index).momentum.z, mc.at(mc_index ).mass);
            result.push_back(leg_lv.P());
        }
        else {
            cout << "MC track not found!" << endl;
        }
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


Vec_f leptonResolution(Vec_rp leptons, Vec_i recind, Vec_i mcind, Vec_rp reco, Vec_mc mc, int mode=0) {
    Vec_f result;
    result.reserve(leptons.size());

    for(int i = 0; i < leptons.size(); ++i) {
        TLorentzVector reco_;
        reco_.SetXYZM(leptons[i].momentum.x, leptons[i].momentum.y, leptons[i].momentum.z, leptons[i].mass);
        int track_index = leptons[i].tracks_begin;
        int mc_index = FCCAnalyses::ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        if(mc_index >= 0 && mc_index < (int)mc.size()) {
            TLorentzVector mc_;
            mc_.SetXYZM(mc.at(mc_index).momentum.x, mc.at(mc_index).momentum.y, mc.at(mc_index).momentum.z, mc.at(mc_index).mass);
            if(mode == 0) result.push_back(reco_.P()/mc_.P());
            else if(mode == 1) result.push_back(reco_.Theta()/mc_.Theta());
            else if(mode == 2) result.push_back(reco_.Phi()/mc_.Phi());
        }
    } 
    return result;
}


struct gen_sel_pdgIDInt {
    gen_sel_pdgIDInt(int arg_pdg, bool arg_chargeconjugate);
    int m_pdg = 13;
    bool m_chargeconjugate = true;
    ROOT::VecOps::RVec<int>  operator() (ROOT::VecOps::RVec<edm4hep::MCParticleData> in);
};

gen_sel_pdgIDInt::gen_sel_pdgIDInt(int arg_pdg, bool arg_chargeconjugate) : m_pdg(arg_pdg), m_chargeconjugate( arg_chargeconjugate )  {};
ROOT::VecOps::RVec<int>  gen_sel_pdgIDInt::gen_sel_pdgIDInt::operator() (ROOT::VecOps::RVec<edm4hep::MCParticleData> in) {
    ROOT::VecOps::RVec<int> result;
    for(size_t i = 0; i < in.size(); ++i) {
        auto & p = in[i];
        if(m_chargeconjugate) {
            if(std::abs( p.PDG) == std::abs(m_pdg)) result.push_back(i);
        }
        else {
            if(p.PDG == m_pdg) result.push_back(i);
        }
    }
    return result;
}

// return list of pdg from decay of a list of mother particle
std::vector<int> gen_decay_list(ROOT::VecOps::RVec<int> mcin, ROOT::VecOps::RVec<edm4hep::MCParticleData> in, ROOT::VecOps::RVec<int> ind) {

   std::vector<int> result;


   // i = index of a MC particle in the Particle block
   // in = the Particle collection
   // ind = the block with the indices for the daughters, Particle#1.index

   // returns a vector with the indices (in the Particle block) of the daughters of the particle i

   for (size_t i = 0; i < mcin.size(); ++i) {
        for (size_t j = 0; j < MCParticle::get_list_of_particles_from_decay(mcin[i],in,ind).size(); ++j) {
            if(in[MCParticle::get_list_of_particles_from_decay(mcin[i],in,ind)[j]].PDG != 25) {
                result.push_back(in[MCParticle::get_list_of_particles_from_decay(mcin[i], in, ind)[j]].PDG);
            }
        }
   }
   return result;
}


Vec_i getRecoMCPDGID(Vec_rp leptons, Vec_i recind, Vec_i mcind, Vec_rp reco, Vec_mc mc) {
    Vec_i result;
    result.reserve(leptons.size());

    //std::cout << "******************" << std::endl;
    //std::cout << "leptons=" << leptons.size() << " recind=" << recind.size() << " mcind=" << mcind.size() << " reco=" << reco.size() << " mc=" << mc.size() << std::endl; 
    for(int i = 0; i < leptons.size(); ++i) {
        TLorentzVector reco_;
        reco_.SetXYZM(leptons[i].momentum.x, leptons[i].momentum.y, leptons[i].momentum.z, leptons[i].mass);
        int track_index = leptons[i].tracks_begin;
        int mc_index = FCCAnalyses::ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        if(mc_index >= 0 && mc_index < (int)mc.size()) {
            result.push_back(mc.at(mc_index).PDG);
        }
    } 
    return result;
}

    
// FSR
std::vector<int> FSR(ROOT::VecOps::RVec<edm4hep::MCParticleData> mc, ROOT::VecOps::RVec<int> parents, ROOT::VecOps::RVec<int> daugther) {

   std::vector<int> result;

    cout << "*****************************" << endl;
   // i = index of a MC particle in the Particle block
   // in = the Particle collection
   // ind = the block with the indices for the daughters, Particle#1.index

   // returns a vector with the indices (in the Particle block) of the daughters of the particle i

   for (size_t i = 0; i < mc.size(); ++i) {
       
        if(mc.at(i).PDG != 22) continue;
       
        cout << "idx=" << i << " " << " status=" << mc.at(i).generatorStatus  << " parent=" << parents.at(i) << " PDGID=" << mc.at(parents.at(i)).PDG  << " daugher=" << daugther.at(i) << " PDGID=" << mc.at(daugther.at(i)).PDG << endl;
        
   }
   return result;
}
    
// for a given MC index, it returns whether or not one of these muons come (indirectly) from a Higgs decay
bool from_Higgsdecay(int i, ROOT::VecOps::RVec<edm4hep::MCParticleData> in, ROOT::VecOps::RVec<int> ind) {

    bool ret = false;
    // i = index of a MC particle in the Particle block
    // in = the Particle collection
    // ind = the block with the indices for the parents, Particle#0.index

    // returns whether the particle i comes from the chain containing the Higgs

    if ( i < 0 || i >= in.size() ) return ret;

    int db = in.at(i).parents_begin;
    int de = in.at(i).parents_end;
  
    //std::cout << "Chain for " << in.at(i).PDG << std::endl;
    //std::cout << "Chain for " << in.at(i).PDG << std::endl;
    //std::cout << "Chain for idx=" << i << " with PDG=" << in.at(i).PDG << " having db=" << db << " and de=" << de << std::endl;
    

    if(db == de) return false; // top of tree
    
   
    for(int id = db; id < de; id++) { // loop over all parents

        int iparent = ind.at(id);
        //std::cout << " Analyze parent idx=" << iparent << " PDG=" << in.at(iparent).PDG << std::endl;
        
        if(std::abs(in.at(iparent).PDG) == 25) ret = true; // if Higgs is found
        else ret = from_Higgsdecay(iparent, in, ind); // otherwise go up in the decay tree
    }
    
    return ret;
}




// for a given lepton collection (legs), it returns whether or not one of these muons come (indirectly) from a Higgs decay
int from_Higgsdecay(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs, ROOT::VecOps::RVec<int> recind, ROOT::VecOps::RVec<int> mcind, ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> reco, ROOT::VecOps::RVec<edm4hep::MCParticleData> mc, ROOT::VecOps::RVec<int> parents, ROOT::VecOps::RVec<int> daugther) {
    
    int ret = 0;
    for (size_t i = 0; i < legs.size(); ++i) {
        
        int track_index = legs[i].tracks_begin;
        int mc_index = ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        if(from_Higgsdecay(mc_index, mc, parents)) {
            ret += 1;
        }
    }
    
    return ret;
}


// for a given muon collection (legs), returns the muons which do not come (indirectly) from a Higgs decay
ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> excluded_Higgs_decays(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs, ROOT::VecOps::RVec<int> recind, ROOT::VecOps::RVec<int> mcind, ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> reco, ROOT::VecOps::RVec<edm4hep::MCParticleData> mc, ROOT::VecOps::RVec<int> parents, ROOT::VecOps::RVec<int> daugther) {
    
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    //result.reserve(in.size());
    for (size_t i = 0; i < legs.size(); ++i) {
        auto & p = legs[i];
        int track_index = legs[i].tracks_begin;
        int mc_index = ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        if(not from_Higgsdecay(mc_index, mc, parents)) {
            result.emplace_back(p);
        }
    }
    return result;
}



// calculate the number of foward leptons
struct polarAngleCategorization {
    polarAngleCategorization(float arg_thetaMin, float arg_thetaMax);
    float thetaMin = 0;
    float thetaMax = 5;
    int operator() (Vec_rp in);
};

polarAngleCategorization::polarAngleCategorization(float arg_thetaMin, float arg_thetaMax) : thetaMin(arg_thetaMin), thetaMax(arg_thetaMax) {};
int polarAngleCategorization::operator() (Vec_rp in) {
    
    int nFwd = 0; // number of forward leptons
    for (size_t i = 0; i < in.size(); ++i) {
        
        auto & p = in[i];
        TLorentzVector lv;
        lv.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        if(lv.Theta() < thetaMin || lv.Theta() > thetaMax) nFwd += 1;
    }
    return nFwd;
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

// for a given MC index, it returns whether or not one of these muons come (indirectly) from a Higgs decay
bool whizard_zh_from_prompt(int i, Vec_mc in, Vec_i ind) {

    bool ret = false;
    // i = index of a MC particle in the Particle block
    // in = the Particle collection
    // ind = the block with the indices for the parents, Particle#0.index

    // returns whether the particle i comes from the chain containing the Higgs

    if ( i < 0 || i >= in.size() ) return ret;

    int db = in.at(i).parents_begin;
    int de = in.at(i).parents_end;
  
    //std::cout << "Chain for " << in.at(i).PDG << std::endl;
    //std::cout << "Chain for " << in.at(i).PDG << std::endl;
    //std::cout << "Chain for idx=" << i << " with PDG=" << in.at(i).PDG << " having db=" << db << " and de=" << de << std::endl;
    

    if(db == de) return true; // top of tree

   
    for(int id = db; id < de; id++) { // loop over all parents

        int iparent = ind.at(id);
        //std::cout << " Analyze parent idx=" << iparent << " PDG=" << in.at(iparent).PDG << std::endl;
        
        //if(std::abs(in.at(iparent).PDG) == 11) ret = true; // if prompt
        if(iparent == 0) return true;
        else if(std::abs(in.at(iparent).PDG) == 25) ret = false; // non prompt, from Higgs decays
        else ret = whizard_zh_from_prompt(iparent, in, ind); // otherwise go up in the decay tree
    }
    
    return ret;
}


// returns the gen particles with given PDGID (absolute) that have the e+/e- as parent, i.e. from prompt
// in Whizard, the prompt leptons from the collision have two parents, the electron and positron
Vec_rp whizard_zh_select_prompt_leptons(Vec_rp in, Vec_i recind, Vec_i mcind, Vec_rp reco, Vec_mc mc, Vec_i parents, Vec_i daugther) {
    Vec_rp result;
    for (size_t i = 0; i < in.size(); ++i) {
        int track_index = in[i].tracks_begin;
        int mc_index = FCCAnalyses::ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        if(whizard_zh_from_prompt(mc_index, mc, parents)) {
            result.emplace_back(in[i]);
        }
    }
    return result;
} 
   
   
   
// perturb the momentum scale with a given constant
struct lepton_momentum_scale {
    lepton_momentum_scale(float arg_scaleunc);
    float scaleunc = 1.;
    Vec_rp operator() (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in);
};

lepton_momentum_scale::lepton_momentum_scale(float arg_scaleunc) : scaleunc(arg_scaleunc) {};
Vec_rp lepton_momentum_scale::operator() (Vec_rp in) {
    Vec_rp result;
    result.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
        auto & p = in[i];
        p.momentum.x = p.momentum.x*(1. + scaleunc);
        p.momentum.y = p.momentum.y*(1. + scaleunc);
        p.momentum.z = p.momentum.z*(1. + scaleunc);
        result.emplace_back(p);
    }
    return result;
}



}