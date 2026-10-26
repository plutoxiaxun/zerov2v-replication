"""Offline regression tests; run with python3 -B scripts/test_revision.py."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from analyze_revision import DATA, analyze, indexed
import audit_public_release
from plot_public_figures import source_request_percent


class RevisionTests(unittest.TestCase):
    def test_sparse_figure_uses_percent_not_gib(self):
        self.assertAlmostEqual(source_request_percent(
            {'source_read_gib': '6.331', 'allocated_capacity_gib': '50'}), 12.662)
        self.assertAlmostEqual(source_request_percent(
            {'source_read_gib': '13.079', 'allocated_capacity_gib': '500'}), 2.6158)
        with self.assertRaises(ValueError):
            source_request_percent({'source_read_gib': '1', 'allocated_capacity_gib': '0'})

    def test_primary_claims(self):
        r = analyze()
        self.assertAlmostEqual(r['M1paired']['reductionPercent'],48.6962776479)
        self.assertEqual(r['M1paired']['exactSignflipP'],0.0625)
        self.assertAlmostEqual(r['R1_C_minus_A']['difference']['mean'],0.7)
        self.assertEqual(r['S1paired']['exactSignflipP'],2/1024)
        self.assertEqual([r['concurrency'][str(w)]['complete'] for w in [1,2,4]],[5,5,4])
        self.assertEqual([round(r['concurrency'][str(w)]['meanPairedRatio'],2) for w in [1,2,4]],[1,1.50,1.99])
        self.assertEqual([round(r['services'][o]['matchedReductionPercent'],2) for o in ['centos7','win2016']],[93.06,58.04])
        self.assertEqual(round(r['model']['heldout_db-D']['MAPEPercent'],2),66.25)
        self.assertEqual(r['selection']['correct'],4)
        self.assertEqual(r['selection']['regretSeconds'],1502)
        self.assertEqual(r['diagnosisPaired']['exactSignflipP'],.25)
        self.assertEqual(round(r['confirmationSensitivity']['confirmation']['reductionPercent'],2),61.56)
        self.assertEqual(r['currentWorksetTargetPhase']['staging']['median'],3729)
        self.assertEqual(r['currentWorksetTargetPhase']['direct']['median'],25)
        self.assertEqual(r['currentWorksetTargetPhase']['adjacent_direct_control']['median'],25)

    def test_duplicate_pairs_rejected(self):
        with self.assertRaises(AssertionError):
            indexed([{'pair':1},{'pair':1}],('pair',))

    def test_changed_source_bytes_rejected(self):
        original = json.loads
        def changed(text, *args, **kwargs):
            value = original(text, *args, **kwargs)
            if isinstance(value,dict) and 'diagnosis' in value:
                value = copy.deepcopy(value)
                next(r for r in value['diagnosis'] if r['mode']=='D')['sourceReadBytes'] += 1
            return value
        with patch('analyze_revision.json.loads',side_effect=changed):
            with self.assertRaises(AssertionError):
                analyze()

    def test_outcome_boundaries(self):
        c = json.loads((DATA/'revision/outcomes.json').read_text())['campaigns']
        self.assertEqual(c['P1Heldout']['originalFormalFailuresPreserved'],2)
        self.assertEqual(c['D1r']['unassistedOriginalFullAcceptance'],10)
        self.assertFalse(c['F1r']['groupCreateSameJobRecoverySupported'])
        self.assertEqual(c['F1r']['finalCbtSameJobRecoveries'],3)


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.package = Path(temp.name)
        for name in ('CITATION.cff', 'RELEASE_STATUS.json',
                     'LICENSE-APACHE-2.0.txt', 'LICENSE-CC-BY-4.0.txt'):
            shutil.copy2(audit_public_release.PACKAGE / name, self.package / name)
        context = patch.object(audit_public_release, 'PACKAGE', self.package)
        context.start()
        self.addCleanup(context.stop)

    def failures(self):
        failures = []
        audit_public_release.audit_release_metadata(failures)
        return failures

    def test_formal_version_with_supplied_doi(self):
        status = json.loads((self.package / 'RELEASE_STATUS.json').read_text())
        self.assertEqual(status['version'], '1.1.0')
        self.assertEqual(status['previousPublicVersion'], '1.0.2')
        self.assertFalse(status['publicUploadPerformed'])
        self.assertEqual(status['newVersionDOI'], '10.5281/zenodo.23667792')
        self.assertFalse(status['doiVerification']['publicAvailabilityVerified'])
        self.assertEqual(self.failures(), [])

    def test_mismatched_version_rejected(self):
        citation = self.package / 'CITATION.cff'
        citation.write_text(citation.read_text().replace('version: 1.1.0', 'version: 1.0.2'))
        self.assertIn('Citation and release-status versions must match', self.failures())

    def test_prerelease_suffix_rejected(self):
        path = self.package / 'RELEASE_STATUS.json'
        status = json.loads(path.read_text())
        status['version'] = '1.1.0-rc1'
        path.write_text(json.dumps(status))
        self.assertIn('Release version must not contain a prerelease suffix', self.failures())

    def test_old_doi_cannot_describe_unpublished_release(self):
        status = json.loads((self.package / 'RELEASE_STATUS.json').read_text())
        citation = self.package / 'CITATION.cff'
        citation.write_text(citation.read_text() + '\ndoi: ' + status['previousArchiveDOI'] + '\n')
        self.assertIn('Citation DOI must match the supplied new-version DOI', self.failures())

    def test_unverified_doi_does_not_imply_publication_date(self):
        citation = self.package / 'CITATION.cff'
        citation.write_text(citation.read_text() + '\ndate-released: 2026-10-26\n')
        self.assertIn('Unverified publication must not invent a release date', self.failures())


if __name__ == '__main__':
    unittest.main()
