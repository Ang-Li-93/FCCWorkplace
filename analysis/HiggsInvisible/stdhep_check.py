#!/usr/bin/env python

import sys
from pyLCIO.drivers.Driver import Driver
#from ROOT import EVENT, IOIMPL
from PDG import pdgid_to_name
#import PDG


class _Truthtmp(object):
   pass
def dump_one_truth (t, id0, f=sys.stdout):
   v = t.getLorentzVec()
   da = list(t.getDaughters())
   d = _Truthtmp()
   d.bc = t.id() - id0
   pdg = t.getPDG()
   d.name = pdgid_to_name (pdg)
   d.da1 = da[0].id()-id0 if len(da)>0 else 0
   d.da2 = da[1].id()-id0 if len(da)>1 else 0
   d.da3 = da[2].id()-id0 if len(da)>2 else 0
   d.da4 = da[3].id()-id0 if len(da)>3 else 0
   d.m = v.M()
   d.px = v.Px()
   d.py = v.Py()
   d.pz = v.Pz()
   d.pt = v.Pt()
   d.phi = v.Phi()
   d.eta = v.Eta()
   d.e = v.Energy()

   stat = t.getGeneratorStatus()
   d.stat = stat

   print ("%(bc)3d %(name)-4s %(da1)4s %(da2)4s %(da3)4s %(da4)4s %(pt)6.1f %(eta)5.2f %(phi)5.2f %(m)5.1f %(px)6.1f %(py)6.1f %(pz)6.1f %(e)6.1f %(stat)d" % d.__dict__, file=f)
   return


class Dumper( Driver ):
   def startOfData (self):
       self.n = 0
   def processEvent (self, event):
       if self.n%1 == 0: print ('---', self.n, event.getEventNumber())
       self.n = self.n + 1
       mcParticles = event.getMcParticles()
       id0 = mcParticles[0].id()-1
       for p in mcParticles:
           dump_one_truth (p, id0)
       return
   def endOfData (self):
       pass


def loop (infile, n = -1, skip = 0):
   from pyLCIO.io.EventLoop import EventLoop
   eventLoop = EventLoop()
   eventLoop.addFile( infile )

   dumper = Dumper()
   eventLoop.add( dumper )

   eventLoop.skipEvents( skip )
   eventLoop.loop( n )
   return


import sys
infile = sys.argv[1]
#infile = '../data/whizard/zh_nneenn.1011_500/zh_nneenn.1011_500.stdhep'
loop (infile, n=100)