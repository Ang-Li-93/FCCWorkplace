#ifndef FCCPhysicsFunctionsGen_H
#define FCCPhysicsFunctionsGen_H

namespace FCCAnalyses {

Vec_i getIndex(Vec_rp in, Vec_rp reco, bool verbose=false) {
    Vec_i result;
    if(verbose) cout << "GET INDEX" << endl;
    for(auto & p: in) {
        if(verbose) cout << " TARGET " << p.energy << endl;
        for(int i = 0; i < reco.size(); ++i) {
            if(verbose) cout << "   PROBE " << reco[i].energy << endl;
            // match on energy, for charged particles can match on track index
            if(reco[i].energy == p.energy) {
                //cout << i << " " << reco[i].energy << " " <<  p.energy << " " << endl;
                result.push_back(i);
                if(verbose) cout << "   FOUND " << i << endl;
                break;
            }
        }
    }
    return result;
}


bool test(Vec_i recind, Vec_i mcind, Vec_rp reco, Vec_mc mc, Vec_rp in) {
    //std::cout << "****************************************" << endl;
    /*
    for(int i = 0; i < reco.size(); ++i) {
 
        int index_mc = mcind[recind[i]];
        auto mc_ = mc[index_mc];
        TLorentzVector mc_p4;
        mc_p4.SetXYZM(mc_.momentum.x, mc_.momentum.y, mc_.momentum.z, mc_.mass);
            
        auto reco_ = reco[i];
        TLorentzVector reco_p4;
        reco_p4.SetXYZM(reco_.momentum.x, reco_.momentum.y, reco_.momentum.z, reco_.mass);
        //std::cout << reco_p4.E() << " " << mc_p4.E() << std::endl;
   
    }*/

    //std::cout << "PHOTONS" << endl;
    Vec_i in_idx = getIndex(in, reco);
    cout << "getIndex=" << in_idx[0] << " " << in_idx[1] << endl;
    cout << "reco=" << reco.size() << " mc=" << mc.size() << " recind=" << recind.size() << " mcind=" << mcind.size() << endl;
    //if(in_idx.size() != in.size()) {
    for(int i = 0; i < in.size(); ++i) {
        
        //cout << " A " << i << " " << in_idx.size() << endl;
        //cout << " B " << in_idx[i] << " " << recind.size() << endl;
        //cout << " C " << recind[in_idx[i]] << " " << mcind.size() << endl;
        //cout << " D " << mcind[recind[in_idx[i]]] << " " << mc.size() << endl;
        int index_mc = mcind[recind[in_idx[i]]];
        
        //std::cout << in_idx.size() << "  " << in.size() << endl;
        //std::cout << index_mc << "  " << recind.size() << endl;
        
        //auto mc_ = mc[index_mc];
        
        cout << index_mc << " " << mc.size() << endl;
        
        if(index_mc > mc.size()) {
            in_idx = getIndex(in, reco, true);
        }
        TLorentzVector mc_p4;
        mc_p4.SetXYZM(mc.at(index_mc).momentum.x, mc.at(index_mc).momentum.y, mc.at(index_mc).momentum.z, mc.at(index_mc).mass);
        /*
        auto reco_ = in[i];
        
        TLorentzVector reco_p4;
        reco_p4.SetXYZM(reco_.momentum.x, reco_.momentum.y, reco_.momentum.z, reco_.mass);
        
        if(mc_p4.E() < 5) {
            std::cout << reco_p4.E() << " " << mc_p4.E() << "  " << mc_.PDG <<  std::endl;
        }
        */
    }
    //}
    bool t = true;
    return t;
}




Vec_rp smearPhotonEnergyResolution(Vec_rp in, Vec_i in_idx, Vec_i recind, Vec_i mcind, Vec_rp reco, Vec_mc mc) {

    // avoid events that have the extra soft photon and screws up the MC/RECO collections
    if(reco.size() != recind.size()) return in;


    // IDEA default
    auto ecal_res_formula = new TF1("ecal_res", "TMath::Sqrt(x^2*0.005^2 + x*0.03^2 + 0.002^2)", 0, 1000); // 0.03=constant term (A), 0.005=stochastic term (B) 0.002=noise term (C)
    //auto ecal_res_formula = new TF1("ecal_res", "TMath::Sqrt(x^2*0.005^2 + x*0.01^2 + 0.002^2)", 0, 1000); // stochastic term S=1%
    //auto ecal_res_formula = new TF1("ecal_res", "TMath::Sqrt(x^2*0.005^2 + x*0.02^2 + 0.002^2)", 0, 1000); // stochastic term S=2%
    //auto ecal_res_formula = new TF1("ecal_res", "TMath::Sqrt(x^2*0.005^2 + x*0.05^2 + 0.002^2)", 0, 1000); // stochastic term S=5%
    //auto ecal_res_formula = new TF1("ecal_res", "TMath::Sqrt(x^2*0.005^2 + x*0.10^2 + 0.002^2)", 0, 1000); // stochastic term S=10%
    //auto ecal_res_formula = new TF1("ecal_res", "TMath::Sqrt(x^2*0.005^2 + x*0.25^2 + 0.002^2)", 0, 1000); // stochastic term S=25%
    //auto ecal_res_formula = new TF1("ecal_res", "TMath::Sqrt(x^2*0.005^2 + x*0.50^2 + 0.002^2)", 0, 1000); // stochastic term S=50%

    // Dual readout
    //auto ecal_res_formula = new TF1("ecal_res", "TMath::Sqrt(x^2*0.01^2 + x*0.11^2 + 0.05^2)", 0, 1000);

    float scale = 1.0; // additional scaling

    Vec_rp result;
    result.reserve(in.size());
    for(int i = 0; i < in.size(); ++i) {
        auto & p = in[i];
        edm4hep::ReconstructedParticleData p_new = p;
        TLorentzVector reco_p4;
        reco_p4.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);

        int mc_index = mcind[recind[in_idx[i]]]; //DOES NOT WORK???
        if(mc_index >= 0 && mc_index < (int)mc.size()) {
            TLorentzVector mc_p4;
            mc_p4.SetXYZM(mc.at(mc_index).momentum.x, mc.at(mc_index).momentum.y, mc.at(mc_index).momentum.z, mc.at(mc_index).mass);
            float new_energy = reco_p4.E();
            if(abs(reco_p4.E()-mc_p4.Energy())/mc_p4.Energy() > 5) { // avoid extreme variations
                std::cout << "MC-RECO MISMATCH: MC_E=" << mc_p4.Energy() << " RECO_E=" << reco_p4.Energy() << std::endl;
            }
            else {
                float res = ecal_res_formula->Eval(mc_p4.Energy())*scale;
                new_energy = gRandom->Gaus(mc_p4.Energy(), res);
            }

            p_new.energy = new_energy;
            // recompute momentum magnitude
            float smeared_p = std::sqrt(p_new.energy * p_new.energy - reco_p4.M() * reco_p4.M());

            // recompute mom x, y, z using original reco particle direction
            p_new.momentum.x = smeared_p * std::sin(reco_p4.Theta()) * std::cos(reco_p4.Phi());
            p_new.momentum.y = smeared_p * std::sin(reco_p4.Theta()) * std::sin(reco_p4.Phi());
            p_new.momentum.z = smeared_p * std::cos(reco_p4.Theta());
        }
        result.push_back(p_new);
    }
    return result;
}


Vec_f photonResolution(Vec_rp in, Vec_i in_idx, Vec_i recind, Vec_i mcind, Vec_rp reco, Vec_mc mc, int mode=0) {
    Vec_f result;

    // avoid events that have the extra soft photon and screws up the MC/RECO collections
    if(reco.size() != recind.size()) return result;

    result.reserve(in.size());

    for(int i = 0; i < in.size(); ++i) {
        TLorentzVector reco_p4;
        reco_p4.SetXYZM(in[i].momentum.x, in[i].momentum.y, in[i].momentum.z, in[i].mass);
        int mc_index = mcind[recind[in_idx[i]]];
        if(mc_index >= 0 && mc_index < (int)mc.size()) {
            TLorentzVector mc_;
            mc_.SetXYZM(mc.at(mc_index).momentum.x, mc.at(mc_index).momentum.y, mc.at(mc_index).momentum.z, mc.at(mc_index).mass);
            //cout << reco_p4.P() << " " << mc_.P()<< " "  << reco_p4.Theta() << " " << mc_.Theta() << " "  << reco_p4.Phi() << " " << mc_.Phi() << endl;
            if(mode == 0) result.push_back(reco_p4.P()/mc_.P());
            else if(mode == 1) result.push_back(reco_p4.Theta()/mc_.Theta());
            else if(mode == 2) result.push_back(reco_p4.Phi()/mc_.Phi());
        }
    } 
    return result;
}

// make Lorentz vectors for a given MC particle collection
Vec_tlv makeLorentzVectors(Vec_mc in) {
    Vec_tlv result;
    for(auto & p: in) {
        TLorentzVector tlv;
        tlv.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
        result.push_back(tlv);
    }
    return result;
}

Vec_mc getRP2MC(Vec_rp in, ROOT::VecOps::RVec<int> recind, ROOT::VecOps::RVec<int> mcind, ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> reco, ROOT::VecOps::RVec<edm4hep::MCParticleData> mc) {
    Vec_mc result;
    for (auto & p: in) {
        int track_index = p.tracks_begin;
        int mc_index = ReconstructedParticle2MC::getTrack2MC_index(track_index, recind, mcind, reco);
        if(mc_index >= 0 && mc_index < mc.size() ) {
            result.push_back(mc.at(mc_index));
        }
        else {
            cout << "MC track not found!" << endl;
        }
    }
    return result;
}

Vec_mc get_gen_pdg(Vec_mc mc, int pdgId, bool abs=true, bool stable=true) {
   Vec_mc result;
   for(size_t i = 0; i < mc.size(); ++i) {
        auto & p = mc[i];
        if(!((abs and std::abs(p.PDG) == pdgId) or (not abs and p.PDG == pdgId))) continue;
        if(stable && p.generatorStatus != 1) continue;
        result.emplace_back(p);
        //if((abs and std::abs(p.PDG) == pdgId) or (not abs and p.PDG == pdgId)) result.emplace_back(p);
   }
   return result;
}

}


#endif