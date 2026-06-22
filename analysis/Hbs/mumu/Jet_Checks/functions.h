#ifndef JETCHECK_FUNCTIONS_H
#define JETCHECK_FUNCTIONS_H
// Custom helpers for the H->bb ME-decay vs Pythia6-resonance-decay m(bb) check.
#include <cmath>
#include <vector>
#include <set>
#include "ROOT/RVec.hxx"
#include "TLorentzVector.h"
#include "edm4hep/MCParticleData.h"
#include "edm4hep/ReconstructedParticleData.h"

namespace JetCheck {

using ROOT::VecOps::RVec;

inline double Emc(const edm4hep::MCParticleData &p) {
  const double px = p.momentum.x, py = p.momentum.y, pz = p.momentum.z, m = p.mass;
  return std::sqrt(px*px + py*py + pz*pz + m*m);
}
inline float mass4(double E, double X, double Y, double Z) {
  const double m2 = E*E - X*X - Y*Y - Z*Z;
  return m2 > 0 ? std::sqrt(m2) : -std::sqrt(-m2);
}

// indices of the first bare b (PDG 5) and first bbar (PDG -5) in the gen record
inline std::pair<int,int> hard_bb(const RVec<edm4hep::MCParticleData> &mc) {
  int ib = -1, ibb = -1;
  for (size_t i = 0; i < mc.size(); ++i) {
    if (mc[i].PDG == 5  && ib  < 0) ib  = (int)i;
    else if (mc[i].PDG == -5 && ibb < 0) ibb = (int)i;
  }
  return {ib, ibb};
}

// (a) parton-level invariant mass of the hard b + bbar
inline float hard_bb_mass(const RVec<edm4hep::MCParticleData> &mc) {
  auto bb = hard_bb(mc);
  if (bb.first < 0 || bb.second < 0) return -1;
  const auto &b = mc[bb.first]; const auto &a = mc[bb.second];
  return mass4(Emc(b)+Emc(a), b.momentum.x+a.momentum.x,
               b.momentum.y+a.momentum.y, b.momentum.z+a.momentum.z);
}

// (b)/(b') particle-level: sum of stable particles, always excluding muons;
// keepNu=false drops neutrinos (visible, MET-blind), true keeps them (MET-corrected)
inline float gen_system_mass(const RVec<edm4hep::MCParticleData> &mc, bool keepNu) {
  double E=0,X=0,Y=0,Z=0;
  for (const auto &p : mc) {
    if (p.generatorStatus != 1) continue;
    const int a = std::abs(p.PDG);
    if (a == 13) continue;
    if (!keepNu && (a==12 || a==14 || a==16)) continue;
    E += Emc(p); X += p.momentum.x; Y += p.momentum.y; Z += p.momentum.z;
  }
  return mass4(E,X,Y,Z);
}

inline void collect_stable(int i, const RVec<edm4hep::MCParticleData> &mc,
                           const RVec<int> &dind, std::vector<int> &acc, std::set<int> &seen) {
  const auto &p = mc[i];
  for (int k = (int)p.daughters_begin; k < (int)p.daughters_end; ++k) {
    if (k < 0 || k >= (int)dind.size()) continue;
    const int j = dind[k];
    if (j < 0 || j >= (int)mc.size() || seen.count(j)) continue;
    seen.insert(j);
    if (mc[j].generatorStatus == 1) acc.push_back(j);
    else collect_stable(j, mc, dind, acc, seen);
  }
}

// (d) CAUSE: invariant mass of the stable descendants of the hard b and bbar.
// dind = the Particle daughters relation index (Particle#1.index or _Particle_daughters.index)
inline float bdesc_mass(const RVec<edm4hep::MCParticleData> &mc, const RVec<int> &dind) {
  auto bb = hard_bb(mc);
  if (bb.first < 0 || bb.second < 0) return -1;
  std::vector<int> acc; std::set<int> seen;
  seen.insert(bb.first); seen.insert(bb.second);
  collect_stable(bb.first,  mc, dind, acc, seen);
  collect_stable(bb.second, mc, dind, acc, seen);
  double E=0,X=0,Y=0,Z=0;
  for (int j : acc) { E+=Emc(mc[j]); X+=mc[j].momentum.x; Y+=mc[j].momentum.y; Z+=mc[j].momentum.z; }
  return mass4(E,X,Y,Z);
}

// m(jj + MET): the two Durham jet 4-vectors (from compute_tlv_jets) plus the
// missing 4-vector, by plain TLorentzVector addition. The Delphes MissingET
// branch is unreadable by RDF in these files (its covMatrix[10] leaf is an
// unsupported "leaf count + static length" type), so the missing 4-momentum is
// reconstructed from the visible ReconstructedParticles: p_miss = (sqrts - E_vis,
// -p_vis). MET carries the escaping-neutrino momentum -> recovers the full
// H->bb mass.
inline float dijet_met_mass(const RVec<TLorentzVector> &jp4,
                            const RVec<float> &rpx, const RVec<float> &rpy,
                            const RVec<float> &rpz, const RVec<float> &re,
                            float sqrts) {
  if (jp4.size() < 2) return -1;
  double vx=0,vy=0,vz=0,vE=0;
  for (size_t i=0;i<rpx.size();++i){ vx+=rpx[i]; vy+=rpy[i]; vz+=rpz[i]; vE+=re[i]; }
  TLorentzVector met; met.SetPxPyPzE(-vx, -vy, -vz, sqrts - vE);
  TLorentzVector tot = jp4[0] + jp4[1] + met;
  return tot.M();
}

// ---- muon-pair (Z) checks at gen level ------------------------------------
inline TLorentzVector mc_tlv(const edm4hep::MCParticleData &p) {
  TLorentzVector v; v.SetPxPyPzE(p.momentum.x, p.momentum.y, p.momentum.z, Emc(p)); return v;
}

// pick the mu- (pdg 13) and mu+ (pdg -13). hard=true -> first in the record
// (the hard-process muons); hard=false -> leading-momentum stable muons (the
// Z muons after FSR; soft b->mu muons are sub-leading).
inline std::pair<int,int> pick_muons(const RVec<edm4hep::MCParticleData> &mc, bool hard) {
  int im=-1, ip=-1;
  if (hard) {
    for (size_t i=0;i<mc.size();++i) {
      if      (mc[i].PDG== 13 && im<0) im=(int)i;
      else if (mc[i].PDG==-13 && ip<0) ip=(int)i;
    }
  } else {
    double pm=-1, pp=-1;
    for (size_t i=0;i<mc.size();++i) {
      if (mc[i].generatorStatus!=1) continue;
      const double p=std::sqrt(mc[i].momentum.x*mc[i].momentum.x+
                               mc[i].momentum.y*mc[i].momentum.y+
                               mc[i].momentum.z*mc[i].momentum.z);
      if      (mc[i].PDG== 13 && p>pm){ pm=p; im=(int)i; }
      else if (mc[i].PDG==-13 && p>pp){ pp=p; ip=(int)i; }
    }
  }
  return {im,ip};
}

// dimuon invariant mass m(mu+ mu-)
inline float dimuon_mass(const RVec<edm4hep::MCParticleData> &mc, bool hard) {
  auto pr=pick_muons(mc,hard); if (pr.first<0||pr.second<0) return -1;
  return (mc_tlv(mc[pr.first])+mc_tlv(mc[pr.second])).M();
}

// recoil mass against the dimuon: m( (sqrts,0,0,0) - mu+mu- )
inline float dimuon_recoil(const RVec<edm4hep::MCParticleData> &mc, bool hard, float sqrts) {
  auto pr=pick_muons(mc,hard); if (pr.first<0||pr.second<0) return -1;
  TLorentzVector z = mc_tlv(mc[pr.first])+mc_tlv(mc[pr.second]);
  TLorentzVector rec; rec.SetPxPyPzE(-z.Px(), -z.Py(), -z.Pz(), sqrts - z.E());
  return rec.M();
}

} // namespace JetCheck
#endif
