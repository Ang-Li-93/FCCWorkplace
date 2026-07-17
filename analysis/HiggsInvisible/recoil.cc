#include "FCCAnalyses/ReconstructedParticle.h"
#include "FCCAnalyses/defines.h"
#include <cmath>


using FCCAnalyses::Vec_rp;
using FCCAnalyses::Vec_mc;
using FCCAnalyses::Vec_f;
using Vec_cl = ROOT::VecOps::RVec<edm4hep::ClusterData>;


template <class T>
TLorentzVector tlv (const T& p)
{
  TLorentzVector v;
  v.SetXYZM(p.momentum.x, p.momentum.y, p.momentum.z, p.mass);
  return v;
}


/////////////////////////////////////////////////////////////////////////////
// ReconstructedParticle operations


Vec_rp merge (Vec_rp a, const Vec_rp& b)
{
  for (const auto& p : b)
    a.emplace_back (p);
  return a;
}


TLorentzVector sum (const Vec_rp& v)
{
  TLorentzVector ret;
  for (const auto& p : v) {
    ret += tlv(p);
  }
  return ret;
}


struct sel_type {
  int m_id;
  sel_type (int id) : m_id(id) {}
  Vec_rp operator() (Vec_rp in)
  {
    Vec_rp result;
    result.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
      auto & p = in[i];
      if (std::abs(p.type) == m_id) {
        result.emplace_back(p);
      }
    }
    return result;
  }
};


struct sel_leps {
  sel_leps (int id) : m_id (id) {}
  Vec_rp operator() (Vec_rp in)
  {
    Vec_rp result;
    result.reserve(in.size());
    int typ1 = 0;
    for (size_t i = 0; i < in.size(); ++i) {
      auto & p = in[i];
      if (std::abs(p.type) == m_id) {
        if (typ1 == 0) {
          result.emplace_back(p);
          typ1 = p.type;
        }
        else if (typ1 == -p.type) {
          result.emplace_back(p);
          typ1 = -999999;
        }
      }
    }
    return result;
  }
  int m_id;
};


struct calc_trues_recoil
{
  Vec_rp
  operator() (float trues, const Vec_rp& in)
  {
    return FCCAnalyses::ReconstructedParticle::recoilBuilder(trues)(in);
  }
};



class coneIsolation
{
public:
  coneIsolation (float dr_min = 0.01, float dr_max = 0.5)
    : m_dr_min (dr_min), m_dr_max (dr_max)
  {}

  Vec_f operator() (const Vec_rp& parts, const Vec_rp& all_rp);


private:
  float m_dr_min;
  float m_dr_max;
};


Vec_f coneIsolation::operator() (const Vec_rp& parts, const Vec_rp& all_rp)
{
  Vec_f out;
  out.reserve (parts.size());

  for (const auto& p : parts) {
    double isosum = 0;
    TLorentzVector p_tlv = tlv (p);
    for (const auto& p2 : all_rp) {
      TLorentzVector p2_tlv = tlv (p2);
      double dr = p_tlv.DeltaR (p2_tlv);
      if (dr > m_dr_min && dr < m_dr_max)
        isosum += p2_tlv.P();
    }
    out.push_back (isosum / p_tlv.P());
  }

  return out;
}


Vec_rp sel_iso (float thresh,
                const Vec_rp& leps,
                const Vec_f& iso)
{
  Vec_rp out;
  out.reserve (leps.size());
  for (size_t i = 0; i < leps.size(); i++) {
    if (iso[i] < thresh)
      out.push_back (leps[i]);
  }
  return out;
}


std::vector<int> get_nclust (const Vec_rp& pv)
{
  std::vector<int> out;
  out.reserve (pv.size());
  for (const auto& p : pv) {
    out.push_back (p.clusters_end - p.clusters_begin);
  }
  return out;
}


std::vector<int> get_ntrack (const Vec_rp& pv)
{
  std::vector<int> out;
  out.resize (pv.size());
  for (const auto& p : pv) {
    out.push_back (p.tracks_end - p.tracks_begin);
  }
  return out;
}



/////////////////////////////////////////////////////////////////////////////
// Brem recovery


struct PhotonLeptonMatch
{
  PhotonLeptonMatch (float angle_, float dist_, float lepndx_, float lepid_)
    : angle(angle_), dist(dist_), lepndx(lepndx_), lepid(lepid_) {}
  float angle;
  float dist;
  int lepndx;
  int lepid;
};


std::vector<float> get_match_angle (const std::vector<PhotonLeptonMatch>& mv)
{
  std::vector<float> out;
  out.reserve (mv.size());
  for (const PhotonLeptonMatch& m : mv) {
    out.push_back (m.angle);
  }
  return out;
}


std::vector<float> get_match_dist (const std::vector<PhotonLeptonMatch>& mv)
{
  std::vector<float> out;
  out.reserve (mv.size());
  for (const PhotonLeptonMatch& m : mv) {
    out.push_back (m.dist);
  }
  return out;
}


std::vector<PhotonLeptonMatch>
photonLeptonMatch (const Vec_rp& gams, const Vec_rp& leps, const Vec_cl& clusts)
{
  std::vector<PhotonLeptonMatch> ret;
  ret.reserve (gams.size());
  for (size_t i = 0; i < gams.size(); i++) {
    TLorentzVector vgam = tlv (gams[i]);
    float minangle = 999;
    int lepndx = -1;
    int lepid = -999;

    for (size_t j = 0; j < leps.size(); j++) {
      const auto& lep = leps[j];
      TLorentzVector vlep = tlv (lep);
      float angle = vgam.Angle (vlep.Vect());
      if (angle < minangle) {
        minangle = angle;
        lepndx = j;
        lepid = lep.type;
      }
    }

    float dist = 999;
    if (lepndx >= 0) {
      const auto& cl_gam = clusts.at (gams[i].clusters_begin);
      const auto& cl_lep = clusts.at (leps[lepndx].clusters_begin);
      TVector3 v3gam (cl_gam.position.x, cl_gam.position.y, cl_gam.position.z);
      TVector3 v3lep (cl_lep.position.x, cl_lep.position.y, cl_lep.position.z);
      dist = (v3gam - v3lep).Mag();
    }

    ret.emplace_back (minangle, dist, lepndx, lepid);
  }
  return ret;
}


Vec_rp addfsr (const Vec_rp& leps, const Vec_rp& gams,
               const std::vector<PhotonLeptonMatch>& mv,
               float angmax)
{
  Vec_rp out = leps;
  for (size_t i = 0; i < mv.size(); i++) {
    const PhotonLeptonMatch& m = mv[i];
    if (m.angle < angmax) {
      TLorentzVector vsum = tlv (leps[m.lepndx]) + tlv (gams[i]);
      auto& lep = out[m.lepndx];
      lep.momentum.x = vsum.Px();
      lep.momentum.y = vsum.Py();
      lep.momentum.z = vsum.Pz();
    }
  }
  return out;
}


/////////////////////////////////////////////////////////////////////////////
// MCParticle operations


TLorentzVector sum (const Vec_mc& v)
{
  TLorentzVector ret;
  for (const auto& p : v) {
    ret += tlv (p);
  }
  return ret;
}


struct calc_truesqrts
{
  float operator() (const Vec_mc& mcp)
  {
    if (mcp.size() < 4) return 0;
    return std::abs(mcp[2].momentum.z) + std::abs(mcp[3].momentum.z);
  }
};


struct sel_isrgam
{
  Vec_mc
  operator() (const Vec_mc& mcp,
              ROOT::VecOps::RVec<podio::ObjectID> dindex) const;
};


Vec_mc
sel_isrgam::operator()(const Vec_mc& mcp,
                       ROOT::VecOps::RVec<podio::ObjectID> dindex) const
{
  Vec_mc out;
  for (unsigned da = mcp[5].daughters_begin; da <= mcp[5].daughters_end; ++da) {
    unsigned ii = dindex[da].index;
    if (mcp[ii].PDG == 22 && mcp[ii].generatorStatus == 1) {
      out.push_back (mcp[ii]);
      if (out.size() == 2) break;
    }
  }
  return out;
}


float calc_mcisrgamz1 (const Vec_mc& isrgam)
{
  float ret = 0;
  for (const auto& g : isrgam) {
    ret = std::max (ret, g.momentum.z);
  }
  return ret;
}


float calc_mcisrgamz2 (const Vec_mc& isrgam)
{
  float ret = 0;
  for (const auto& g : isrgam) {
    ret = std::min (ret, g.momentum.z);
  }
  return ret;
}


/////////////////////////////////////////////////////////////////////////////
// Matching operations


struct MatchRel
{
  MatchRel (int mc, int rp) : mcndx(mc), rpndx(rp) {}
  int mcndx;
  int rpndx;
};


int matchOne (const edm4hep::MCParticleData& mc,
              const Vec_rp& rps)
{
  int matched = -1;
  float mindr = 0.1;
  TLorentzVector mc_tlv = tlv (mc);
  for (size_t i  = 0; i < rps.size(); i++) {
    const auto& rp = rps[i];
    TLorentzVector rp_tlv = tlv (rp);
    float dr = mc_tlv.DeltaR (rp_tlv);
    if (dr < mindr) {
      mindr = dr;
      matched = i;
    }
  }
  return matched;
}


std::vector<MatchRel>
match (const Vec_mc& mcs, const Vec_rp& rps)
{
  std::vector<MatchRel> ret;
  ret.reserve (mcs.size());
  for (size_t i = 0; i < mcs.size(); i++) {
    const auto& mc = mcs[i];
    int matched = matchOne (mc, rps);
    if (matched >= 0)
      ret.emplace_back (i, matched);
  }
  return ret;
}


Vec_mc
sel_matched (const Vec_mc& mcs,
             const std::vector<MatchRel>& matchrel)
{
  Vec_mc out;
  for (const MatchRel& r : matchrel) {
    out.push_back (mcs[r.mcndx]);
  }
  return out;
}


Vec_mc
sel_unmatched (const Vec_mc& mcs,
               const std::vector<MatchRel>& matchrel)
{
  Vec_mc out;
  for (size_t i = 0; i < mcs.size(); i++) {
    bool found = false;
    for (const MatchRel& r : matchrel) {
      if (i == r.mcndx) {
        found = true;
        break;
      }
    }
    if (!found) {
      out.push_back (mcs[i]);
    }
  }
  return out;
}


/////////////////////////////////////////////////////////////////////////////
// Generic operations


struct recoilBuilder
{
  template <class PART>
  ROOT::VecOps::RVec<PART> 
  operator() (float sqrts, const ROOT::VecOps::RVec<PART>& in);
};


template <class PART>
ROOT::VecOps::RVec<PART>  recoilBuilder::operator() (float sqrts, const ROOT::VecOps::RVec<PART>& in) {
  ROOT::VecOps::RVec<PART> result;
  auto recoil_p4 = TLorentzVector(0, 0, 0, sqrts);
  for (const auto & v1: in) {
    recoil_p4 -= tlv(v1);
  }
  auto recoil_fcc = PART();
  recoil_fcc.momentum.x = recoil_p4.Px();
  recoil_fcc.momentum.y = recoil_p4.Py();
  recoil_fcc.momentum.z = recoil_p4.Pz();
  recoil_fcc.mass = recoil_p4.M();
  result.push_back(recoil_fcc);
  return result;
};


struct recoilBuilder2
{
  template <class PART>
  TLorentzVector
  operator() (float sqrts, const ROOT::VecOps::RVec<PART>& in);

  TLorentzVector
  operator() (float sqrts, const TLorentzVector& in);
};


template <class PART>
TLorentzVector
recoilBuilder2::operator() (float sqrts, const ROOT::VecOps::RVec<PART>& in) {
  auto recoil_p4 = TLorentzVector(0, 0, 0, sqrts);
  for (const auto & v1: in) {
    recoil_p4 -= tlv(v1);
  }
  return recoil_p4;
};


TLorentzVector
recoilBuilder2::operator() (float sqrts, const TLorentzVector& in) {
  auto recoil_p4 = TLorentzVector(0, 0, 0, sqrts);
  recoil_p4 -= in;
  return recoil_p4;
};



struct resonanceBuilder {
  float m_resonance_mass;
  resonanceBuilder(float arg_resonance_mass);
  template <class PART>
  ROOT::VecOps::RVec<PART> operator()(const ROOT::VecOps::RVec<PART>& legs);
};


resonanceBuilder::resonanceBuilder(float arg_resonance_mass) {m_resonance_mass = arg_resonance_mass;}

template <class PART>
ROOT::VecOps::RVec<PART> resonanceBuilder::operator()(const ROOT::VecOps::RVec<PART>& legs) {
  ROOT::VecOps::RVec<PART> result;
  int n = legs.size();
  if (n >1) {
    ROOT::VecOps::RVec<bool> v(n);
    std::fill(v.end() - 2, v.end(), true);
    do {
      PART reso;
      TLorentzVector reso_lv;
      for (int i = 0; i < n; ++i) {
          if (v[i]) {
            reso.charge += legs[i].charge;
            reso_lv += tlv(legs[i]);
          }
      }
      reso.momentum.x = reso_lv.Px();
      reso.momentum.y = reso_lv.Py();
      reso.momentum.z = reso_lv.Pz();
      reso.mass = reso_lv.M();
      result.emplace_back(reso);
    } while (std::next_permutation(v.begin(), v.end()));
  }
  if (result.size() > 1) {
    auto resonancesort = [&] (PART i ,PART j) { return (abs( m_resonance_mass -i.mass)<abs(m_resonance_mass-j.mass)); };
    std::sort(result.begin(), result.end(), resonancesort);
    auto first = result.begin();
    auto last = result.begin() + 1;
    ROOT::VecOps::RVec<PART> onlyBestReso(first, last);
    return onlyBestReso;
  } else {
    return result;
  }
}



template <class PART>
ROOT::VecOps::RVec<PART>
boost (float xang, const ROOT::VecOps::RVec<PART>& parts)
{
  float beta = sin(xang/2);
  ROOT::VecOps::RVec<PART> result;
  for (const PART& p : parts) {
    result.push_back (p);
    TLorentzVector x = tlv(p);
    x.Boost (-beta, 0, 0);
    PART& pp = result.back();
    pp.momentum.x = x.Px();
    pp.momentum.y = x.Py();
    pp.momentum.z = x.Pz();
  }
  return result;
}

