"""Small adversarial controls for the exact native-derived association exception."""
import copy
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('edit_loop', Path(__file__).resolve().parents[1] / 'probes/native_edit_loop.py')
loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loop)


class DerivedAssociationChecks(unittest.TestCase):
    def setUp(self):
        self.before = ET.fromstring('<CDXML><page id="1"><scheme id="2"><step id="3" ReactionStepArrows="41" ReactionStepObjectsAboveArrow="80 81" ReactionStepObjectsBelowArrow="20 82" ReactionStepAtomMap="11 12"/><step id="4" ReactionStepArrows="42"/></scheme></page></CDXML>')

    def check(self, after, expected):
        changed = loop.derived_associations(self.before, after, 20, ['41', '51'])
        equal = loop.tree_value(self.before) == loop.tree_value(after)
        self.assertEqual(equal, expected)
        return changed

    def test_only_target_add_remove_pass_with_exact_receipt(self):
        after = copy.deepcopy(self.before)
        step = after.find('.//step')
        step.set('ReactionStepObjectsAboveArrow', '80 20 81')
        step.set('ReactionStepObjectsBelowArrow', '82')
        result = self.check(after, True)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['before'], '80 81')
        self.assertEqual(result[0]['after'], '80 20 81')

    def test_other_ids_order_duplicate_target_and_other_steps_refuse(self):
        for values in ('80 20 99', '81 20 80', '80 20 20 81'):
            with self.subTest(values=values):
                after = copy.deepcopy(self.before)
                after.find('.//step').set('ReactionStepObjectsAboveArrow', values)
                self.check(after, False)
        after = copy.deepcopy(self.before)
        after.findall('.//step')[1].set('ReactionStepObjectsAboveArrow', '20')
        self.check(after, False)

    def test_arrow_atommap_and_reactants_changes_refuse(self):
        for key, value in [('ReactionStepArrows', '42'), ('ReactionStepArrows', '41 42'),
                           ('ReactionStepAtomMap', '11 99'), ('ReactionStepReactants', '99')]:
            with self.subTest(key=key, value=value):
                after = copy.deepcopy(self.before)
                step = after.find('.//step')
                step.set('ReactionStepObjectsAboveArrow', '80 20 81')
                step.set(key, value)
                self.check(after, False)

    def test_ambiguous_selected_step_refuses(self):
        after = copy.deepcopy(self.before)
        after.find('.//step').set('ReactionStepObjectsAboveArrow', '80 20 81')
        after.findall('.//step')[1].set('ReactionStepArrows', '41')
        self.check(after, False)

    def test_initial_stereo_only_missing_to_N_and_not_arbitrary_atom_changes(self):
        before = ET.fromstring('<CDXML><page id="1"><fragment id="2"><n id="3" Element="8"/><b id="4" B="3" E="5"/><n id="5" AS="R"/></fragment></page></CDXML>')
        after = copy.deepcopy(before)
        after.find('.//n').set('AS', 'N')
        after.find('.//b').set('BS', 'N')
        self.assertEqual(len(loop.initial_stereo_markers(before, after)), 2)
        self.assertEqual(loop.tree_value(before), loop.tree_value(after))
        for tag, index, key, value in [('n', 1, 'AS', 'N'), ('n', 0, 'AS', 'R'), ('n', 0, 'Element', '7')]:
            after = copy.deepcopy(before)
            after.findall('.//' + tag)[index].set(key, value)
            loop.initial_stereo_markers(before, after)
            self.assertNotEqual(loop.tree_value(before), loop.tree_value(after))


if __name__ == '__main__':
    unittest.main()
