"""Observable checks for the portable local evidence reader."""

import json
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
SKILL=REPO/'skills'/'ahang-content-research'
SCRIPT=SKILL/'scripts'/'evidence.py'
DATASET=SKILL/'references'/'evidence.json'

class EvidenceTests(unittest.TestCase):
    def run_cli(self,*args,script=SCRIPT,cwd=None):
        env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
        p=subprocess.run([sys.executable,str(script),*args],cwd=cwd,env=env,encoding='utf-8',capture_output=True)
        return p.returncode,json.loads(p.stdout)

    def changed_dataset(self,mutate):
        data=json.loads(DATASET.read_text(encoding='utf-8'))
        mutate(data)
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        p=Path(directory.name)/'changed.json';p.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        return p

    def test_valid_snapshot_and_distinct_counts(self):
        code,result=self.run_cli('validate')
        self.assertEqual(code,0);self.assertTrue(result['valid'])
        code,s=self.run_cli('stats')
        self.assertEqual(code,0)
        self.assertEqual(s['packaged_evidence_entries'],31)
        self.assertEqual(s['reported_session_observations'],451)
        self.assertFalse(s['first_1500_fulltext_verified'])
        self.assertEqual(s['source_kind_counts']['author_website'],1)
        self.assertEqual(s['reply_entries'],1)

    def test_search_and_read_status_filter(self):
        code,result=self.run_cli('search','多模型')
        self.assertEqual(code,0)
        self.assertIn('E07',{r['evidence_id'] for r in result['records']})
        code,result=self.run_cli('list','--status','preview_only','--limit','3')
        self.assertEqual(code,0)
        self.assertTrue(all(r['read_status']=='preview_only' for r in result['records']))
        self.assertEqual(result['returned_count'],3)
        self.assertIsNotNone(result['next_offset'])

    def test_unknown_id_does_not_return_a_nearby_record(self):
        code,result=self.run_cli('show','E9999')
        self.assertEqual(code,2)
        self.assertIn('E9999',result['ids'])

    def test_duplicate_post_is_rejected(self):
        def mutate(data):
            row=dict(data['records'][0]);row['evidence_id']='E32'
            data['records'].append(row);data['coverage']['packaged_record_count']=32
        path=self.changed_dataset(mutate)
        code,result=self.run_cli('--dataset',str(path),'validate')
        self.assertEqual(code,2)
        self.assertTrue(any('duplicate canonical_post_url' in e for e in result['errors']))

    def test_complete_coverage_cannot_be_inferred_from_selected_entries(self):
        path=self.changed_dataset(lambda d:d['coverage'].update(first_1500_fulltext_verified=True))
        code,result=self.run_cli('--dataset',str(path),'validate')
        self.assertEqual(code,2)
        self.assertTrue(any('coverage' in e for e in result['errors']))

    def test_date_conflict_is_reported(self):
        path=self.changed_dataset(lambda d:d['records'][0].update(date='2025-01-09'))
        code,result=self.run_cli('--dataset',str(path),'validate')
        self.assertEqual(code,2)
        self.assertTrue(any('post ID' in e for e in result['errors']))

    def test_author_site_version_cannot_be_relabeled_as_raw_post(self):
        def mutate(data):
            next(r for r in data['records'] if r['evidence_id']=='E22')['read_status']='detail_text'
        path=self.changed_dataset(mutate)
        code,result=self.run_cli('--dataset',str(path),'validate')
        self.assertEqual(code,2)
        self.assertTrue(any('edited-version' in e for e in result['errors']))

    def test_skill_folder_is_portable_without_repo_or_original_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            portable=Path(temp)/'portable-skill'
            shutil.copytree(SKILL,portable,ignore=shutil.ignore_patterns('__pycache__'))
            code,result=self.run_cli('show','E18','E29',script=portable/'scripts'/'evidence.py',cwd=temp)
            self.assertEqual(code,0)
            self.assertEqual([r['evidence_id'] for r in result['records']],['E18','E29'])
            self.assertIn('reprint',result['records'][1]['excerpt_provenance']['kind'])

if __name__=='__main__':
    unittest.main()
