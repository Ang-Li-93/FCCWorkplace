// Truth summary of e+e- -> Z H, H -> W+ W- events (PLAN.md Sec. 5.2, 5.3): incoming beams, H,
// W+, W-, the W analysers (CONVENTIONS.md Sec. 2) and their partners, and the Z decay products,
// as indices into the MC collection 'Particle' (used by stage1/truth_hww.py).
//
// Two generator records are handled:
//  - central winter2023 samples (WHIZARD 3.0.3 + PYTHIA6): one H line whose daughters are W+ W-
//    and a single line per W whose daughters are its two fermions;
//  - dedicated samples (gen/run_hwwqe_job.sh: WHIZARD 3.1.5 LHEF -> Pythia 8.310): the H and W
//    resonance lines of the LHEF (status 22).  If Pythia8 lets a W radiate a photon
//    (TimeShower:QEDshowerByOther, on by default, off in config/generation/p8_lhe_hwwqe_ecm240.cmnd),
//    the radiating W and its recoiler are followed by copies (status 51/52) and only the last
//    copy decays.
//
// Slots:
//  - H (slot 2) is the RECORDED H: the H line whose daughters are the W+ W- pair (last copy of the
//    first H in the record).  It is not the physical H rest frame.  In the winter2023 record it is
//    the pre-shower documentation copy with the WHIZARD momentum, which differs from W+ + W- when
//    the shower of the Z decay products rescaled the (Z system, H) pair (LOG.md, 2026-10-15).
//    The physical H frame is the rest frame of W+ + W- (slots 3 + 4).
//  - W+, W- (slots 3, 4) are the decaying (last) copies, so that W = analyser + partner always
//    holds.  In the winter2023 record each W has one copy, so first and last copy coincide.
//  - analysers and partners (slots 5-8) are the two fermion daughters of the decaying W copy,
//    i.e. the fermions before their own final-state radiation (first generation).
//  - Z fermion and antifermion (slots 9, 10) are the fermion siblings of the H (daughters of the
//    first parent of the first H copy), fermion first.
// Slots that are not found keep index -1 (PDG 0 in the output).
#ifndef HWWQE_TRUTH_FUNCTIONS_H
#define HWWQE_TRUTH_FUNCTIONS_H

#include <cstdlib>
#include <vector>

#include "ROOT/RVec.hxx"
#include "edm4hep/MCParticleData.h"

namespace HWWQE {

using Vec_mc = ROOT::VecOps::RVec<edm4hep::MCParticleData>;
using Vec_i = ROOT::VecOps::RVec<int>;

// Slots of the summary, in this order.
enum Slot { BEAM_EM = 0, BEAM_EP, HIGGS, WPLUS, WMINUS, ANA_P, PARTNER_P, ANA_M, PARTNER_M, ZF1, ZF2, NSLOT };

inline std::vector<int> daughters(const Vec_mc &mc, const Vec_i &dau, int i) {
  std::vector<int> out;
  for (unsigned j = mc[i].daughters_begin; j < mc[i].daughters_end; ++j) out.push_back(dau[j]);
  return out;
}

inline std::vector<int> parents(const Vec_mc &mc, const Vec_i &par, int i) {
  std::vector<int> out;
  for (unsigned j = mc[i].parents_begin; j < mc[i].parents_end; ++j) out.push_back(par[j]);
  return out;
}

// Follow copies of a particle (same PDG among its daughters) down to the decaying copy.
inline int last_copy(const Vec_mc &mc, const Vec_i &dau, int i) {
  for (int guard = 0; guard < 100; ++guard) {
    int next = -1;
    for (int d : daughters(mc, dau, i))
      if (mc[d].PDG == mc[i].PDG) next = d;
    if (next < 0) return i;
    i = next;
  }
  return i;
}

// Analyser of the W+: charged antilepton or down-type antiquark; of the W-: their conjugates.
inline bool is_wplus_analyser(int pdg) { return pdg == -11 || pdg == -13 || pdg == -15 || pdg == -1 || pdg == -3 || pdg == -5; }
inline bool is_wminus_analyser(int pdg) { return pdg == 11 || pdg == 13 || pdg == 15 || pdg == 1 || pdg == 3 || pdg == 5; }
inline bool is_fermion(int pdg) { const int a = std::abs(pdg); return a >= 1 && a <= 16; }

// Indices of the summary slots in the MC collection (-1 where not found).
inline Vec_i truth_hww_indices(const Vec_mc &mc, const Vec_i &par, const Vec_i &dau) {
  Vec_i idx(NSLOT, -1);
  for (int i = 0; i < (int)mc.size(); ++i) {           // incoming beams: e-/e+ without parents
    if (mc[i].parents_begin != mc[i].parents_end) continue;
    if (mc[i].PDG == 11 && idx[BEAM_EM] < 0) idx[BEAM_EM] = i;
    if (mc[i].PDG == -11 && idx[BEAM_EP] < 0) idx[BEAM_EP] = i;
  }
  for (int i = 0; i < (int)mc.size() && idx[HIGGS] < 0; ++i) {   // the H that decays to W+ W-
    if (mc[i].PDG != 25) continue;
    const int h = last_copy(mc, dau, i);
    int wp = -1, wm = -1;
    for (int d : daughters(mc, dau, h)) {
      if (mc[d].PDG == 24) wp = d;
      if (mc[d].PDG == -24) wm = d;
    }
    if (wp < 0 || wm < 0) continue;
    idx[HIGGS] = h;                        // recorded H (see the header): not the W+ W- rest frame
    idx[WPLUS] = last_copy(mc, dau, wp);   // decaying W copies: W = analyser + partner
    idx[WMINUS] = last_copy(mc, dau, wm);
    const int slots[2][3] = {{WPLUS, ANA_P, PARTNER_P}, {WMINUS, ANA_M, PARTNER_M}};
    for (const auto &s : slots) {
      for (int d : daughters(mc, dau, idx[s[0]])) {
        if (!is_fermion(mc[d].PDG)) continue;
        const bool ana = (s[0] == WPLUS) ? is_wplus_analyser(mc[d].PDG) : is_wminus_analyser(mc[d].PDG);
        idx[ana ? s[1] : s[2]] = d;
      }
    }
    // Z decay products: fermion siblings of the H (same parents), fermion first
    const auto ph = parents(mc, par, i);
    if (!ph.empty()) {
      for (int d : daughters(mc, dau, ph[0])) {
        if (d == i || !is_fermion(mc[d].PDG)) continue;
        if (mc[d].PDG > 0 && idx[ZF1] < 0) idx[ZF1] = d;
        else if (mc[d].PDG < 0 && idx[ZF2] < 0) idx[ZF2] = d;
      }
    }
  }
  return idx;
}

// The selected particles in slot order; empty slots get a default particle (PDG 0, zero momentum).
inline Vec_mc select(const Vec_mc &mc, const Vec_i &idx) {
  Vec_mc out(idx.size());
  for (size_t k = 0; k < idx.size(); ++k)
    if (idx[k] >= 0) out[k] = mc[idx[k]];
  return out;
}

}  // namespace HWWQE

#endif
