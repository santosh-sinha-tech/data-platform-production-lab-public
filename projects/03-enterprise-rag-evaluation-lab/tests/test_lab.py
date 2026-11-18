"""Hand-authored unit and integration checks; runnable by pytest or unittest."""
import csv
import json
import math
from pathlib import Path
import tempfile
import unittest
from rag_lab.answers import generate
from rag_lab.data import read, chunk_documents, validate
from rag_lab.metrics import evaluate_answer, retrieval_metrics
from rag_lab.retrieval import Index, fuse
from rag_lab.runner import ROOT, run, failure_tags

class LabTests(unittest.TestCase):
    def setUp(self):
        self.docs=read(ROOT/'data/documents.json')['documents']
        self.refs=read(ROOT/'data/references.json')
        self.ledger=read(ROOT/'data/adjudications.json')['claims']
        self.fixtures=read(ROOT/'data/answer_fixtures.json')
        self.q={q['id']:q for q in self.refs['questions']}
        self.chunks=chunk_documents(self.docs,64,8)

    def test_dataset_valid(self):
        validate(self.docs,self.refs,{'claims':self.ledger},self.fixtures)

    def test_invalid_reference_rejected(self):
        self.refs['questions'][0]['relevance']['missing']=3
        with self.assertRaises(AssertionError):
            validate(self.docs,self.refs,{'claims':self.ledger},self.fixtures)

    def test_stable_ids(self):
        self.assertEqual(self.chunks,chunk_documents(self.docs,64,8))
        self.assertEqual(len(self.chunks),len({c.id for c in self.chunks}))
        altered=json.loads(json.dumps(self.docs))
        altered[0]['passages'][0]['text']+=' Changed.'
        self.assertNotEqual(self.chunks[0].id,chunk_documents(altered,64,8)[0].id)
        self.assertEqual(self.chunks[-1].id,chunk_documents(altered,64,8)[-1].id)

    def test_chunk_overlap(self):
        chunks=chunk_documents(self.docs,8,2)
        self.assertEqual(chunks[0].text.split()[-2:],chunks[1].text.split()[:2])
        self.assertTrue(all(c.end-c.start<=8 for c in chunks))
        for size,overlap in [(0,0),(4,4),(4,-1)]:
            with self.assertRaises(ValueError): chunk_documents(self.docs,size,overlap)

    def test_metrics_hand_calculation(self):
        m=retrieval_metrics(['x','a','b'],{'a':3,'b':1},3)
        self.assertEqual(m['recall'],1)
        self.assertEqual(m['precision'],2/3)
        self.assertEqual(m['mrr'],.5)
        self.assertAlmostEqual(m['ndcg'],(7/math.log2(3)+1/math.log2(4))/(7+1/math.log2(3)))
        self.assertEqual(retrieval_metrics([],{},3)['recall'],None)
        self.assertEqual(retrieval_metrics(['x'],{'a':1},3)['mrr'],0)
        with self.assertRaises(ValueError): retrieval_metrics(['a','a'],{'a':1},3)

    def test_rrf_hand_calculation_and_tie(self):
        self.assertEqual(fuse([['a','b'],['b','c']],60),['b','a','c'])
        self.assertEqual(fuse([['b'],['a']],60),['a','b'])
        self.assertEqual(fuse([['a','a','b']]),fuse([['a','b']]))
        with self.assertRaises(ValueError): fuse([['a']],0)

    def test_index_consistency(self):
        index=Index(self.chunks,lexical_fallback=True)
        result=index.search('idle development compute','bm25_local',3)
        self.assertTrue(all(c.id in index.by_id for c in result))
        self.assertIn('cost-v2/idle',[c.passage_id for c in result])
        with self.assertRaises(ValueError): Index(self.chunks+self.chunks,lexical_fallback=True)
        with self.assertRaises(ValueError): index.search('x','unrecognized',3)

    def test_chunk_siblings_collapsed(self):
        index=Index(chunk_documents(self.docs,8,2),lexical_fallback=True)
        result=index.search('orders quality contract','bm25_local',5)
        self.assertEqual(len({c.passage_id for c in result}),5)

    def test_correct_answer_wrong_citation(self):
        f=self.fixtures['answers'][1]
        m=evaluate_answer(f,self.q['q05'],self.ledger)
        self.assertEqual(m['fact_precision'],1)
        self.assertEqual(m['claim_support'],1)
        self.assertEqual(m['citation_precision'],0)
        self.assertEqual(m['citation_coverage'],0)

    def test_partial_support(self):
        m=evaluate_answer(self.fixtures['answers'][3],self.q['q11'],self.ledger)
        self.assertEqual(m['fact_recall'],1)
        self.assertEqual(m['claim_support'],.5)
        self.assertEqual(m['citation_coverage'],.5)
        self.assertEqual(m['citation_precision'],1)

    def test_abstention(self):
        m=evaluate_answer(self.fixtures['answers'][5],self.q['q13'],self.ledger)
        self.assertEqual(m['appropriate_abstention'],1)
        self.assertIsNone(m['claim_support'])
        self.assertEqual(generate('x',[])['abstain'],True)
        m=evaluate_answer(self.fixtures['answers'][-1],self.q['q05'],self.ledger)
        self.assertEqual(m['abstention_correct'],0)

    def test_conflicting_and_stale_evidence(self):
        f=self.fixtures['answers'][4]
        score=evaluate_answer(f,self.q['q05'],self.ledger)
        self.assertEqual(score['contradictions'],1)
        self.assertEqual(score['claim_support'],0)
        self.assertIn('Stale source',failure_tags(f,self.q['q05'],score,f['evidence'],self.docs,self.ledger))
        f=self.fixtures['answers'][6]
        self.assertEqual(evaluate_answer(f,self.q['q12'],self.ledger)['contradictions'],1)
        self.assertTrue(generate('idle',[c for c in self.chunks if c.passage_id=='cost-v1/idle'])['abstain'])

    def test_unknown_claim_not_called_verified(self):
        f={'claims':[{'text':'Unreviewed paraphrase','citations':[]}],'evidence':[],'abstain':False}
        m=evaluate_answer(f,self.q['q05'],self.ledger)
        self.assertEqual(m['unadjudicated_claims'],1)
        self.assertEqual(m['claim_support'],0)

    def test_baseline_no_reference_dependency(self):
        import inspect
        import rag_lab.answers as module
        source=inspect.getsource(module)
        self.assertNotIn('read(',source)
        self.assertNotIn('adjudications',source)
        answer=generate('deliberately unrelated question',self.chunks[:1])
        self.assertEqual(answer['claims'][0]['text'],self.chunks[0].text)

    def test_reproducibility_and_reports(self):
        config=read(ROOT/'config/quick.json')
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ma=run(config,Path(a),True,True)
            mb=run(config,Path(b),True,True)
            self.assertEqual(read(Path(a)/'predictions.json'),read(Path(b)/'predictions.json'))
            self.assertEqual(ma['answers'],mb['answers'])
            for key in ['recall','precision','mrr','ndcg']:
                self.assertEqual(ma['retrieval']['bm25_local'][key],mb['retrieval']['bm25_local'][key])
            for file in ['metrics.json','retrieval_comparison.csv','answer_evaluation.csv','failure_analysis.md','benchmark_report.md','latency_samples.csv']:
                self.assertGreater((Path(a)/file).stat().st_size,0)
            with (Path(a)/'retrieval_comparison.csv').open() as stream:
                rows=list(csv.DictReader(stream))
            self.assertAlmostEqual(ma['retrieval']['bm25_local']['recall'],sum(float(r['recall']) for r in rows)/len(rows))
            self.assertEqual(ma['skipped_methods'],['dense','hybrid'])

if __name__=='__main__':
    unittest.main()
