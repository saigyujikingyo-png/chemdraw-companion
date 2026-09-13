import copy,sys,tempfile,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'probes')]
from verify_native_masks import records,same_records,mixed_contact_evidence


class MaskReadbackChecks(unittest.TestCase):
    def test_font_inheritance_mapping_and_curve_fields(self):
        xml='<CDXML LabelFont="3" CaptionFont="3" LabelSize="8"><fonttable><font id="3" name="Arial" charset="iso-8859-1"/></fonttable><page><n id="2" p="0 0"><t><s>O</s></t></n><curve id="4" ArrowheadWidth="163" CurveType="8"/></page></CDXML>'
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.cdxml';source.write_text(xml);baseline=records(source)
            for tag,key,value in [('curve','ArrowheadWidth','999'),('curve','CurveType','0'),('s','font','99'),('font','name','Other'),('CDXML','LabelSize','12')]:
                root=ET.fromstring(xml);next(root.iter(tag)).set(key,value);changed=Path(d)/'changed.cdxml';ET.ElementTree(root).write(changed)
                try:equal=same_records(baseline,records(changed))
                except ValueError:equal=False
                with self.subTest(field=key):self.assertFalse(equal)
            self.assertTrue(same_records(baseline,records(source)))

    def test_run_stays_bound_to_its_atom(self):
        xml='<CDXML LabelFont="3" LabelSize="8"><fonttable><font id="3" name="Arial"/></fonttable><n id="1"><t><s>O</s></t></n><n id="2"><t><s>N</s></t></n></CDXML>'
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.cdxml';b=Path(d)/'b.cdxml';a.write_text(xml);root=ET.fromstring(xml);x,y=root.findall('n/t/s');x.text,y.text=y.text,x.text;ET.ElementTree(root).write(b)
            self.assertFalse(same_records(records(a),records(b)))

    def test_consistent_font_identity_renaming_preserves_effective_font(self):
        xml='<CDXML LabelFont="3" LabelSize="8"><fonttable><font id="3" name="Arial"/></fonttable><n id="1"><t><s font="3">O</s></t></n></CDXML>'
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.cdxml';b=Path(d)/'b.cdxml';a.write_text(xml);b.write_text(xml.replace('"3"','"19"'))
            self.assertTrue(same_records(records(a),records(b)))

    def test_third_object_cannot_borrow_allowed_circle(self):
        groups=[{'native_id':str(i),'rgb':c} for i,c in enumerate(([200,0,0],[0,200,0],[0,0,200]))];palette=np.array([g['rgb'] for g in groups]);points=np.array([[0,0]]);bounds=np.ones((1,3),dtype=bool)
        regions=[{'objects':['0','1'],'name':'shared_atom','center':np.array([0,0]),'radius_px':10}]
        unresolved,receipt=mixed_contact_evidence(points,np.array([[100,100,0]]),palette,bounds,groups,regions)
        self.assertEqual(unresolved,0);self.assertEqual(receipt[0]['contributor_object_ids'],['0','1'])
        for pixel in ([100,0,100],[0,100,100],[67,67,67]):
            unresolved,_=mixed_contact_evidence(points,np.array([pixel]),palette,bounds,groups,regions)
            self.assertEqual(unresolved,1)

    def test_ambiguous_colour_contributors_fail_closed(self):
        groups=[{'native_id':str(i),'rgb':c} for i,c in enumerate(([200,0,0],[0,200,0],[100,100,0]))];palette=np.array([g['rgb'] for g in groups])
        regions=[{'objects':['0','1'],'name':'shared_atom','center':np.array([0,0]),'radius_px':10}]
        unresolved,receipt=mixed_contact_evidence(np.array([[0,0]]),np.array([[50,150,0]]),palette,np.ones((1,3),dtype=bool),groups,regions)
        self.assertEqual(unresolved,1);self.assertEqual(receipt[0]['contributor_object_ids'],['0','1','2'])


if __name__=='__main__':unittest.main()
