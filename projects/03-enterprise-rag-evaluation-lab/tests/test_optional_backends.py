"""Real package/model checks explicitly gated for offline test runs."""
import importlib.util
import os
import unittest
from rag_lab.data import read, chunk_documents
from rag_lab.retrieval import Index
from rag_lab.runner import ROOT

class OptionalBackendTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('rank_bm25'), 'rank-bm25 not installed')
    def test_library_bm25(self):
        chunks=chunk_documents(read(ROOT/'data/documents.json')['documents'],64,8)
        result=Index(chunks).search('development idle compute','bm25',3)
        self.assertIn('cost-v2/idle',[c.passage_id for c in result])

    @unittest.skipUnless(os.getenv('RAG_TEST_DENSE')=='1', 'Set RAG_TEST_DENSE=1 with installed dependencies and pinned model')
    def test_dense_and_hybrid(self):
        chunks=chunk_documents(read(ROOT/'data/documents.json')['documents'],64,8)
        index=Index(chunks,'all')
        self.assertEqual(index.vectors.shape,(len(chunks),384))
        for method in ['dense','hybrid']:
            result=index.search('development idle compute shutdown',method,3)
            self.assertEqual(len(result),3)
            self.assertEqual(result,index.search('development idle compute shutdown',method,3))
            self.assertIn('cost-v2/idle',[c.passage_id for c in result])
