#ifndef FCCANALYZER_ZH_MASS_XSEC_GEN_H
#define FCCANALYZER_ZH_MASS_XSEC_GEN_H

#include "defines.h"

namespace FCCAnalyses {
    
    
// returns the gen particles with given PDGID (absolute) that have the e+/e- as parent, i.e. from prompt
// in Whizard, the prompt leptons from the collision have two parents, the electron and positron
float mll_gen_leps(ROOT::VecOps::RVec<edm4hep::MCParticleData> mc, ROOT::VecOps::RVec<int> parents, ROOT::VecOps::RVec<int> daughters) {

    //cout << "-----------" << endl;
    
    // get Higgs
    int higgs_parent_idx = -1;
    for(size_t i = 0; i < mc.size(); ++i) {
        if(higgs_parent_idx != -1) break;
        auto & p = mc[i];
        if(std::abs(p.PDG) != 25) continue;
        for(unsigned j = p.parents_begin; j != p.parents_end; ++j) {
            
            higgs_parent_idx = parents.at(j);
            break;
        }
    }
    
    TLorentzVector d1;
    TLorentzVector d2;
    int i = 0;
    for(unsigned j = mc.at(higgs_parent_idx).daughters_begin; j != mc.at(higgs_parent_idx).daughters_end; ++j) {
        
        auto & p = mc.at(daughters.at(j));
        if(p.PDG == 25) continue;
        if(i == 0) d1.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        if(i == 1) d2.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        i++;
    }
    
    //cout << d1.Theta() << "  " << d2.Theta() << " " << d1.DeltaR(d2) << endl;

    return (d1+d2).M();
} 
    
// returns the gen particles with given PDGID (absolute) that have the e+/e- as parent, i.e. from prompt
// in Whizard, the prompt leptons from the collision have two parents, the electron and positron
float deltaR_gen_leps(ROOT::VecOps::RVec<edm4hep::MCParticleData> mc, ROOT::VecOps::RVec<int> parents, ROOT::VecOps::RVec<int> daughters) {

    //cout << "-----------" << endl;
    
    // get Higgs
    int higgs_parent_idx = -1;
    for(size_t i = 0; i < mc.size(); ++i) {
        if(higgs_parent_idx != -1) break;
        auto & p = mc[i];
        if(std::abs(p.PDG) != 25) continue;
        for(unsigned j = p.parents_begin; j != p.parents_end; ++j) {
            
            higgs_parent_idx = parents.at(j);
            break;
        }
    }
    
    TLorentzVector d1;
    TLorentzVector d2;
    int i = 0;
    for(unsigned j = mc.at(higgs_parent_idx).daughters_begin; j != mc.at(higgs_parent_idx).daughters_end; ++j) {
        
        auto & p = mc.at(daughters.at(j));
        if(p.PDG == 25) continue;
        if(i == 0) d1.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        if(i == 1) d2.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        i++;
    }
    
    //cout << d1.Theta() << "  " << d2.Theta() << " " << d1.DeltaR(d2) << endl;

    return d1.DeltaR(d2);
} 

    
// returns the gen particles with given PDGID (absolute) that have the e+/e- as parent, i.e. from prompt
// in Whizard, the prompt leptons from the collision have two parents, the electron and positron
bool is_VBF(ROOT::VecOps::RVec<edm4hep::MCParticleData> mc, ROOT::VecOps::RVec<int> parents, ROOT::VecOps::RVec<int> daughters) {

    cout << "-----------" << endl;
    
    // get Higgs
    int higgs_parent_idx = -1;
    for(size_t i = 0; i < mc.size(); ++i) {
        if(higgs_parent_idx != -1) break;
        auto & p = mc[i];
        if(std::abs(p.PDG) != 25) continue;
        for(unsigned j = p.parents_begin; j != p.parents_end; ++j) {
            
            cout << " PARENT PDGID=" << mc.at(parents.at(j)).PDG  << endl;
            higgs_parent_idx = parents.at(j);
            break;
        }
    }
    
    TLorentzVector d1;
    TLorentzVector d2;
    int i = 0;
    for(unsigned j = mc.at(higgs_parent_idx).daughters_begin; j != mc.at(higgs_parent_idx).daughters_end; ++j) {
        
        auto & p = mc.at(daughters.at(j));
        if(i == 0) d1.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        if(i == 1) d2.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        i++;
    }
    
    cout << d1.Theta() << "  " << d2.Theta() << " " << d1.DeltaR(d2) << endl;

    
    return false;
    for(size_t i = 0; i < mc.size(); ++i) {
        auto & p = mc[i];
        //if(std::abs(p.PDG) != 12) continue;
        //if(std::abs(mc.at(parents.at(i)).PDG) == 11) return true;
        cout << "PDGID=" << p.PDG << endl;
        
        for(unsigned j = p.daughters_begin; j != p.daughters_end; ++j) {
            cout << " DAUGHTER PDGID=" << mc.at(daughters.at(j)).PDG  << endl;
        }
        
        /*
        for(unsigned j = p.parents_begin; j != p.parents_end; ++j) {
            //cout << "  -> idx=" << " PDGID=" << mc.at(parents.at(j)).PDG  << endl;
            //if(std::abs(mc.at(parents.at(j)).PDG) == 11) {
             //   if(abs(p.PDG) == 12 or abs(mc.at(parents.at(j)).PDG) == 12) {
                cout << " PARENT PDGID=" << mc.at(parents.at(j)).PDG  << endl;
                //return true;
               // }
            //}
        }
        */
        
        //cout << "idx=" << i << " " << " status=" << mc.at(i).generatorStatus  << " parent=" << parents.at(i) << " PDGID=" << mc.at(parents.at(i)).PDG  << endl;
        /*
            for(unsigned j = p.parents_begin; j != p.parents_end; ++j) {
                if(std::abs(in.at(parents.at(j)).PDG) == 11) {
                    result.emplace_back(p);
                    break;
                }
            }
        */
    }
    return false;
} 

    
    
// get the gen p from reco
std::vector<float> gen_p_from_reco(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs, ROOT::VecOps::RVec<int> recind, ROOT::VecOps::RVec<int> mcind, ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> reco, ROOT::VecOps::RVec<edm4hep::MCParticleData> mc) {

   std::vector<float> result;

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
    
    
ROOT::VecOps::RVec<edm4hep::MCParticleData> get_photons(ROOT::VecOps::RVec<edm4hep::MCParticleData> mc) {

   ROOT::VecOps::RVec<edm4hep::MCParticleData> result;

   for(size_t i = 0; i < mc.size(); ++i) {
       
        auto & p = mc[i];
        if(p.PDG == 22) result.emplace_back(p);
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


    
    
    
 
// returns the gen particles with given PDGID (absolute) that have the e+/e- as parent, i.e. from prompt
// in Whizard, the prompt leptons from the collision have two parents, the electron and positron
ROOT::VecOps::RVec<edm4hep::MCParticleData> select_prompt_leptons_gen(int m_pdg, ROOT::VecOps::RVec<edm4hep::MCParticleData> in, ROOT::VecOps::RVec<int> parents) {

    ROOT::VecOps::RVec<edm4hep::MCParticleData> result;
    for(size_t i = 0; i < in.size(); ++i) {
        auto & p = in[i];
        if(std::abs(p.PDG) == m_pdg) {
            for(unsigned j = p.parents_begin; j != p.parents_end; ++j) {
                if(std::abs(in.at(parents.at(j)).PDG) == 11) {
                    result.emplace_back(p);
                    break;
                }
            }
        }
    }
    return result;
} 


// returns the gen particle indidex with given PDGID (absolute) that have the e+/e- as parent, i.e. from prompt
// in Whizard, the prompt leptons from the collision have two parents, the electron and positron
ROOT::VecOps::RVec<int> select_prompt_leptons_idx(int m_pdg, ROOT::VecOps::RVec<edm4hep::MCParticleData> in, ROOT::VecOps::RVec<int> parents) {

    ROOT::VecOps::RVec<int> result;
    for(size_t i = 0; i < in.size(); ++i) {
        auto & p = in[i];
        if(std::abs(p.PDG) == m_pdg) {
            for(unsigned j = p.parents_begin; j != p.parents_end; ++j) {
                if(std::abs(in.at(parents.at(j)).PDG) == 11) {
                    result.emplace_back(i);
                    break;
                }
            }
        }
    }
    return result;
}
      
 

ROOT::VecOps::RVec<edm4hep::MCParticleData> gen_merge(ROOT::VecOps::RVec<edm4hep::MCParticleData> in, ROOT::VecOps::RVec<int> idx) {

    ROOT::VecOps::RVec<edm4hep::MCParticleData> result;
    result.reserve(idx.size());
    for (size_t i = 0; i < idx.size(); ++i) {
        auto & p = in[idx[i]];
        result.emplace_back(p);
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





ROOT::VecOps::RVec<int> get_parentids(int mcind, ROOT::VecOps::RVec<edm4hep::MCParticleData> mc, ROOT::VecOps::RVec<int> parents){
  ROOT::VecOps::RVec<int> result;
  /*std::cout <<"================== Full Truth=================" <<std::endl;
  for (size_t i = 0; i < mc.size(); ++i) {
    std::cout << "i= " << i << "  PDGID "<< mc.at(i).PDG  <<  "  status  " << mc.at(i).generatorStatus << std::endl;
    for (unsigned j = mc.at(i).parents_begin; j != mc.at(i).parents_end; ++j)
      std::cout << "   ==index " << j <<" parents " << parents.at(j) << "  PDGID "<< mc.at(parents.at(j)).PDG << "  status  " << mc.at(parents.at(j)).generatorStatus << std::endl;
  }*/

  //std::cout <<"================== NEW EVENT=================" <<std::endl;


    if (mcind<0){
      //result.push_back(-999);
      //continue;
    }
    //std::cout << "mc ind " << mcind.at(i) << "  PDGID "<< mc.at(mcind.at(i)).PDG  << "  status  " << mc.at(mcind.at(i)).generatorStatus << std::endl;
    for (unsigned j = mc.at(mcind).parents_begin; j != mc.at(mcind).parents_end; ++j) {
      //std::cout << "   ==index " << j <<" parents " << parents.at(j) << "  PDGID "<< mc.at(parents.at(j)).PDG << "  status  " << mc.at(parents.at(j)).generatorStatus << std::endl;
       result.push_back(parents.at(j));
    }
    //std::cout << mc.at(mcind.at(i)).parents_begin <<"---"<< mc.at(mcind.at(i)).parents_end<< std::endl;
    /*
    if (mc.at(mcind).parents_end - mc.at(mcind).parents_begin>1) {
      std::cout << "-999 "  << (mc.at(mcind).parents_end - mc.at(mcind).parents_begin)  << std::endl;
      result.push_back(-999);
    }
    else {
      //std::cout << "not -999 "<< parents.at(mc.at(mcind.at(i)).parents_begin) << std::endl;
      result.push_back(parents.at(mc.at(mcind).parents_begin));
    }
    */

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






































    /*
std::vector<int> get_list_of_stable_particles_from_decay( int i, ROOT::VecOps::RVec<edm4hep::MCParticleData> in, ROOT::VecOps::RVec<int> ind) {

  std::vector<int> res;
  // i = index of a MC particle in the Particle block
  // in = the Particle collection
  // ind = the block with the indices for the daughters, Particle#1.index

  // returns a vector with the indices (in the Particle block) of the stable daughters of the particle i,
  // from the complete decay chain.

  if ( i < 0 || i >= in.size() ) return res;

  int db = in.at(i).daughters_begin ;
  int de = in.at(i).daughters_end; // always -1
  
  //std::cout << "Chain for " << in.at(i).PDG << std::endl;
  //std::cout << "Chain for " << in.at(i).PDG << std::endl;
  std::cout << "Chain for idx=" << i << " with PDG=" << in.at(i).PDG << " having nDaughters=" << (de-db) << std::endl;
    

  if ( db != de ) {// particle is unstable
    //int d1 = ind[db] ;
    //int d2 = ind[de-1];
    //for (int idaughter = d1; idaughter <= d2; idaughter++) {
    for (int id = db; id < de; id++) { // loop over all daughers
        //int idaughter = ind[ id ];
        int idaughter = ind.at(id);
        std::cout << " Analyze daugher " << in.at(idaughter).PDG <<  std::endl;
        std::vector<int> rr = get_list_of_stable_particles_from_decay( idaughter, in, ind) ;
        res.insert( res.end(), rr.begin(), rr.end() );
    }
  }
  else {    // particle is stable
     res.push_back( i ) ;
     return res ;
  }
  return res;
}

bool from_Higgsdecay(int i, ROOT::VecOps::RVec<edm4hep::MCParticleData> in, ROOT::VecOps::RVec<int> ind) {

    bool ret = false;
    std::vector<int> res;
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








int compare(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> f1, ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> f2) {

    if(f1.size() != f2.size()) {
        std::cout << "not equal size " << std::endl;
        return 2;
        }
    if(f1.size() > 0) {
    
        if((f1.at(0).mass - f2.at(0).mass) > 0.001) {
        
            std::cout << "no equal mass " << f1.at(0).mass << " " << f2.at(0).mass << std::endl;
            return 1;
        }
    
    }
    
    
    return 0;
}



ROOT::VecOps::RVec<int> from_higgs_decay(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs,
				ROOT::VecOps::RVec<int> recind ,
				ROOT::VecOps::RVec<int> mcind ,
				ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> reco ,
				ROOT::VecOps::RVec<edm4hep::MCParticleData> mc,
                ROOT::VecOps::RVec<int> parents,
                ROOT::VecOps::RVec<int> daugthers)   {

    ROOT::VecOps::RVec<int> result;
    //ROOT::VecOps::RVec<float> muon_pt = ReconstructedParticle::get_pt(legs);
    int n = legs.size();
    //std::cout << "nMuons=" << n << std::endl;
    for(int i = 0; i < n; i++) { // loop over muon collection
    
        // get associated MC index of the RECO muon
        int track_index = legs[i].tracks_begin ;   // index in the Track array    
        int mc_index = ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco); // MC index of the muon
  
        bool ret = from_Higgsdecay(mc_index, mc, parents);
        result.emplace_back(ret);
        
        //std::cout << " fromHiggs=" << ret << " pT=" << muon_pt.at(i) << std::endl;
        
    }
    return result;
}

// returns the muon collection which comes from Higgs decays
ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> muon_from_higgs_decay(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs, ROOT::VecOps::RVec<int> from_higgs)   {

    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    int n = legs.size();
    for(int i = 0; i < n; i++) {
    
        if(from_higgs.at(i) == 1) result.emplace_back(legs.at(i));
    }
    //std::cout << "TOT=" << n << " fromHiggs=" << result.size() << std::endl;
    return result;
}

// returns the muon collection which comes  not from Higgs decays
ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> muon_not_from_higgs_decay(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> legs, ROOT::VecOps::RVec<int> from_higgs)   {

    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    int n = legs.size();
    for(int i = 0; i < n; i++) {
    
        if(from_higgs.at(i) == 0) result.emplace_back(legs.at(i));
    }
    //std::cout << "TOT=" << n << " fromHiggs=" << result.size() << std::endl;
    return result;
}


ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> selectPair(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> pairs)   {

    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    if(pairs.size() == 0) return result;
    
    if(pairs.size() == 1) {
    
        result.emplace_back(pairs.at(0));
        return result;
    }

    int idx_min = -1;
    float d_min = 9e9;
    //std::cout << "------------" << std::endl;
    for(int i = 0; i < pairs.size(); ++i) {
     
        // calculate recoil
        auto recoil_p4 = TLorentzVector(0, 0, 0, 240);
        TLorentzVector tv1;
        tv1.SetXYZM(pairs.at(i).momentum.x, pairs.at(i).momentum.y, pairs.at(i).momentum.z, pairs.at(i).mass);
        recoil_p4 -= tv1;
      
        
        //float d = std::pow(pairs.at(i).mass - 91.2, 2);
        //float d = std::pow(recoil_p4.M() - 125.0, 2);
        float d = std::pow(pairs.at(i).mass - 91.2, 2) / (2*2) + std::pow(recoil_p4.M() - 125.0, 2) / (0.8*0.8);
        
        //std::cout << " m=" << pairs.at(i).mass << " rec=" << recoil_p4.M() << " d=" << d << std::endl;
        if(d < d_min) {
            d_min = d;
            idx_min = i;
        }
    }
    
    //std::cout << idx_min << std::endl;

    //result.emplace_back(pairs.at(idx_min));
    result.emplace_back(pairs.at(0));
    return result;
}
*/








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
   


}

#endif
