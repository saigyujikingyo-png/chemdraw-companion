import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.arrow_ports import atom_ports

class ArrowPorts(unittest.TestCase):
    def test_asymmetric_labels_use_measured_boundary(self):
        center=(0,0);box=(-2,-3,15,4);B=20;extension=5
        for end,u,visible in atom_ports(center,box,B,extension):
            boundary=tuple(visible[k]-B*.14*u[k] for k in (0,1))
            self.assertTrue(any(abs(boundary[k]-box[k+offset])<1e-8 for k in (0,1) for offset in (0,2)))
            self.assertAlmostEqual(math.dist(end,visible),extension)
            self.assertFalse(box[0]<=visible[0]<=box[2] and box[1]<=visible[1]<=box[3])

    def test_unlabelled_atom_and_translation(self):
        a=list(atom_ports((0,0),None,18,4));b=list(atom_ports((53,-21),None,18,4))
        for (p,_,q),(r,_,s) in zip(a,b):
            self.assertAlmostEqual(math.dist(q,(0,0)),3)
            for k,d in enumerate((53,-21)):self.assertAlmostEqual(r[k]-p[k],d);self.assertAlmostEqual(s[k]-q[k],d)

if __name__=='__main__':unittest.main()
