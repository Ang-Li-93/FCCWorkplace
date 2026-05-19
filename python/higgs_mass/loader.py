
import sys, os, glob, shutil, json, math, re, random
import ROOT
import functions

ROOT.gROOT.SetBatch()
ROOT.ROOT.EnableImplicitMT()



print ("Load default cxx analyzers ... ")
ROOT.gSystem.Load("libedm4hep")
ROOT.gSystem.Load("libpodio")
ROOT.gSystem.Load("libFCCAnalyses")
ROOT.gErrorIgnoreLevel = ROOT.kFatal
_edm  = ROOT.edm4hep.ReconstructedParticleData()
_pod  = ROOT.podio.ObjectID()
_fcc  = ROOT.dummyLoader

print ("Load custom cxx analyzers ... ")
if "/functions.so" not in ROOT.gSystem.GetLibraries(): ROOT.gSystem.CompileMacro("macros/functions.cc", "k")
