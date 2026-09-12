import copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('edit_checker',ROOT/'probes/verify_native_edits.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def evidence():
    before={'snapshot_version':'native-scene/0.2','warnings':0,'style':{'line_width':.6},
      'atoms':[{'id':1,'type':'atom','element':6,'charge':0,'implicit_h':3,'isotope':0,'radical':0,'stereo':0,'node_type':0,'number':'7','label':'C','x':20,'y':20},
               {'id':2,'type':'atom','element':8,'charge':0,'implicit_h':1,'isotope':0,'radical':0,'stereo':0,'node_type':0,'number':'8','label':'OH','x':34.4,'y':20}],
      'bonds':[{'id':3,'type':'bond','a':1,'b':2,'order':1,'display':0,'display2':0,'stereo':0}],
      'curves':[{'id':20,'type':'spline','num_points':6,'head':2,'tail':0,'head_type':1,'line_type':0,'fill_type':0,'head_size':650,'head_width':160,'points':[0.,1.,0.,1.,2.,3.,4.,5.,6.,7.,6.,7.]}],
      'symbols':[{'id':10,'type':'symbol','symbol_type':0,'is_radical':True,'is_charge':False,'points':[20.,12.,22.,12.]}],
      'captions':[{'id':30,'type':'caption','text':'Caption','anchor':[10.,18.],'left':10.,'top':10.,'family':'Arial','size':8,'face':0,'angle':0,'styles':[{'family':'Arial','size':8,'face':0}]}],
      'arrows':[{'id':40,'type':'arrow','start':[50.,20.],'end':[80.,20.],'head':2,'tail':0,'head_type':1,'line_type':0,'head_size':900,'head_width':250}]}
    intent={'version':'native-edit-intent/0.2','atom_translation':{'ids':[1],'dx':3.,'dy':0.},'symbol_translations':[{'id':10,'deltas':[3.,0.,3.,0.]}],'curve_changes':[{'id':20,'deltas':[3.,0.,3.,0.,2.,-.75,1.,0.,0.,0.,0.,0.]}],'caption_replacements':[{'id':30,'from':'Caption','to':'Caption [edited]'}]}
    edited=copy.deepcopy(before);edited['atoms'][0]['x']=23.;edited['symbols'][0]['points']=[23.,12.,25.,12.];edited['curves'][0]['points']=[3.,1.,3.,1.,4.,2.25,5.,5.,6.,7.,6.,7.];edited['captions'][0]['text']='Caption [edited]'
    diagnostic=copy.deepcopy(edited);diagnostic['atoms'][0]['charge']=1;diagnostic['atoms'][0]['label']='C+';diagnostic['symbols']=[];diagnostic['captions'][0]['text']='Diagnostic';diagnostic['warnings']=1
    diagnostic_intent={'version':'native-edit-intent/0.2','charge_change':{'id':1,'from':0,'to':1},'removed_symbol_id':10,'caption_replacements':[{'id':30,'from':'Caption [edited]','to':'Diagnostic'}]}
    events=[]
    for ext in ('cdx','cdxml'):
        for stage,detail in [('before',before),('motion_intent',intent),('motion_edited',edited),('motion_reopened',edited),('diagnostic_intent',diagnostic_intent),('diagnostic_edited',diagnostic),('diagnostic_reopened',diagnostic)]:events.append({'stage':stage+'_'+ext,'detail':copy.deepcopy(detail)})
    return events


class EditIntentChecks(unittest.TestCase):
    def test_exact_declared_changes_pass(self):
        self.assertEqual([r['native_edit_save_reopen'] for r in checker.verify_events(evidence())['results']],['pass','pass'])

    def test_noop_curve_symbol_caption_setters_fail(self):
        events=evidence();original=events[0]['detail']
        for e in events:
            if e['stage'].startswith(('motion_edited','motion_reopened')):
                for key in ('curves','symbols','captions'):e['detail'][key]=copy.deepcopy(original[key])
        self.assertTrue(all(r['native_edit_save_reopen']=='failed' for r in checker.verify_events(events)['results']))

    def test_undeclared_chemistry_and_missing_head_fail(self):
        for kind,property,value in [('atoms','implicit_h',4),('atoms','stereo',1),('atoms','charge',.01),('bonds','order',2),('curves','head',0),('symbols','symbol_type',3)]:
            with self.subTest(kind=kind,property=property):
                events=evidence()
                for e in events:
                    if e['stage'].startswith(('motion_edited','motion_reopened')):e['detail'][kind][0][property]=value
                self.assertTrue(all(r['native_edit_save_reopen']=='failed' for r in checker.verify_events(events)['results']))

    def test_wrong_atom_and_new_warning_fail(self):
        events=evidence()
        for e in events:
            if e['stage'].startswith(('motion_edited','motion_reopened')):
                e['detail']['atoms'][0]['x']=20.;e['detail']['atoms'][1]['x']+=3.;e['detail']['warnings']=1
        self.assertTrue(all(r['native_edit_save_reopen']=='failed' for r in checker.verify_events(events)['results']))

    def test_missing_before_or_intent_fails_and_cli_exits_nonzero(self):
        events=[e for e in evidence() if not e['stage'].startswith('motion_intent')]
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);(folder/'events.jsonl').write_text('\n'.join(json.dumps(e) for e in events),encoding='utf-8')
            result=subprocess.run([sys.executable,str(ROOT/'probes/verify_native_edits.py'),str(folder)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertTrue((folder/'edit-verification.json').exists())


if __name__=='__main__':unittest.main()
