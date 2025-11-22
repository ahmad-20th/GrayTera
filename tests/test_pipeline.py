import unittest
from core.pipeline import Pipeline
from core.data_store import DataStore
from core.target import Target
import tempfile
import shutil


class TestPipeline(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.data_store = DataStore(self.temp_dir)
        self.pipeline = Pipeline(self.data_store)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_pipeline_initialization(self):
        self.assertEqual(len(self.pipeline.stages), 3)
        self.assertEqual(self.pipeline.current_stage_index, 0)
    
    def test_target_creation(self):
        target = Target(domain="example.com")
        self.assertEqual(target.domain, "example.com")
        self.assertEqual(len(target.subdomains), 0)
    
    # Add more tests...


if __name__ == '__main__':
    unittest.main()
