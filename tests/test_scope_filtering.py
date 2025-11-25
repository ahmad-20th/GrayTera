"""
Unit tests for scope filtering feature
"""
import unittest
import json
import tempfile
from pathlib import Path
from utils.scope_filter import ScopeFilter
from stages.scope_filtering import ScopeFilteringStage
from core.target import Target


class TestScopeFilter(unittest.TestCase):
    """Test ScopeFilter utility class"""
    
    def setUp(self):
        """Create test scope file"""
        self.test_scope = {
            "in_scope": {
                "domains": [
                    "example.com",
                    "www.example.com",
                    "api.example.com",
                    "*.internal.example.com"
                ],
                "patterns": [
                    "^prod-[a-z0-9-]+\\.example\\.com$"
                ]
            },
            "out_of_scope": {
                "domains": [
                    "test.example.com",
                    "staging.example.com"
                ],
                "patterns": [
                    ".*-dev\\.example\\.com$"
                ]
            }
        }
        
        # Create temporary scope file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_scope, self.temp_file)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test file"""
        Path(self.temp_file.name).unlink()
    
    def test_load_scope_file(self):
        """Test loading scope from file"""
        scope = ScopeFilter(self.temp_file.name)
        self.assertTrue(scope.loaded)
        self.assertEqual(len(scope.in_scope), 4)
        self.assertEqual(len(scope.out_of_scope), 2)
    
    def test_exact_domain_matching(self):
        """Test exact domain matching"""
        scope = ScopeFilter(self.temp_file.name)
        
        # In scope exact matches
        self.assertTrue(scope.is_in_scope("example.com"))
        self.assertTrue(scope.is_in_scope("www.example.com"))
        self.assertTrue(scope.is_in_scope("api.example.com"))
        
        # Out of scope exact matches
        self.assertFalse(scope.is_in_scope("test.example.com"))
        self.assertFalse(scope.is_in_scope("staging.example.com"))
    
    def test_wildcard_domain_matching(self):
        """Test wildcard domain matching"""
        scope = ScopeFilter(self.temp_file.name)
        
        # Wildcard matches
        self.assertTrue(scope.is_in_scope("db.internal.example.com"))
        self.assertTrue(scope.is_in_scope("cache.internal.example.com"))
        self.assertTrue(scope.is_in_scope("internal.example.com"))
    
    def test_regex_pattern_matching(self):
        """Test regex pattern matching"""
        scope = ScopeFilter(self.temp_file.name)
        
        # In scope patterns
        self.assertTrue(scope.is_in_scope("prod-api.example.com"))
        self.assertTrue(scope.is_in_scope("prod-db-001.example.com"))
        
        # Out of scope patterns
        self.assertFalse(scope.is_in_scope("feature-dev.example.com"))
        self.assertFalse(scope.is_in_scope("my-dev.example.com"))
    
    def test_subdomain_matching(self):
        """Test subdomain of in-scope domain"""
        scope = ScopeFilter(self.temp_file.name)
        
        # Subdomains of in-scope domains should be in scope
        self.assertTrue(scope.is_in_scope("api.api.example.com"))
        self.assertTrue(scope.is_in_scope("v2.api.example.com"))
    
    def test_filter_subdomains(self):
        """Test filtering a list of subdomains"""
        scope = ScopeFilter(self.temp_file.name)
        
        subdomains = [
            "example.com",
            "www.example.com",
            "api.example.com",
            "test.example.com",
            "staging.example.com",
            "db.internal.example.com",
            "prod-api.example.com",
            "feature-dev.example.com",
            "unknown.com"
        ]
        
        in_scope, out_of_scope = scope.filter_subdomains(subdomains)
        
        expected_in_scope = [
            "example.com",
            "www.example.com",
            "api.example.com",
            "db.internal.example.com",
            "prod-api.example.com"
        ]
        
        expected_out_of_scope = [
            "test.example.com",
            "staging.example.com",
            "feature-dev.example.com",
            "unknown.com"
        ]
        
        self.assertEqual(set(in_scope), set(expected_in_scope))
        self.assertEqual(set(out_of_scope), set(expected_out_of_scope))
    
    def test_no_scope_file(self):
        """Test behavior when no scope file provided"""
        scope = ScopeFilter()
        
        # Without scope loaded, all subdomains should pass
        self.assertTrue(scope.is_in_scope("anything.com"))
        self.assertTrue(scope.is_in_scope("test.example.com"))
        self.assertFalse(scope.loaded)
    
    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive"""
        scope = ScopeFilter(self.temp_file.name)
        
        self.assertTrue(scope.is_in_scope("EXAMPLE.COM"))
        self.assertTrue(scope.is_in_scope("Api.Example.Com"))
        self.assertFalse(scope.is_in_scope("TEST.EXAMPLE.COM"))
    
    def test_get_stats(self):
        """Test getting scope statistics"""
        scope = ScopeFilter(self.temp_file.name)
        stats = scope.get_stats()
        
        self.assertTrue(stats['loaded'])
        self.assertEqual(stats['in_scope_domains'], 4)
        self.assertEqual(stats['out_of_scope_domains'], 2)
        self.assertEqual(stats['patterns'], 2)
    
    def test_invalid_scope_file(self):
        """Test handling of invalid scope file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {")
            invalid_file = f.name
        
        try:
            scope = ScopeFilter(invalid_file)
            self.assertFalse(scope.loaded)
        finally:
            Path(invalid_file).unlink()
    
    def test_out_of_scope_precedence(self):
        """Test that out-of-scope takes precedence over in-scope"""
        scope = ScopeFilter(self.temp_file.name)
        
        # test.example.com is both in scope (as subdomain of example.com)
        # and explicitly out of scope
        self.assertFalse(scope.is_in_scope("test.example.com"))


class TestScopeFilteringStage(unittest.TestCase):
    """Test ScopeFilteringStage integration"""
    
    def setUp(self):
        """Create test scope file and target"""
        self.test_scope = {
            "in_scope": {
                "domains": ["example.com", "*.internal.example.com"],
                "patterns": []
            },
            "out_of_scope": {
                "domains": ["test.example.com"],
                "patterns": []
            }
        }
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.test_scope, self.temp_file)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up"""
        Path(self.temp_file.name).unlink()
    
    def test_stage_filtering(self):
        """Test scope filtering stage execution"""
        stage = ScopeFilteringStage({}, self.temp_file.name)
        
        target = Target(domain='example.com')
        target.subdomains = [
            'api.example.com',
            'test.example.com',
            'db.internal.example.com',
            'unknown.com'
        ]
        
        result = stage.execute(target)
        
        self.assertTrue(result)
        self.assertEqual(len(target.subdomains), 2)
        self.assertIn('api.example.com', target.subdomains)
        self.assertIn('db.internal.example.com', target.subdomains)
        self.assertNotIn('test.example.com', target.subdomains)
        self.assertNotIn('unknown.com', target.subdomains)
    
    def test_stage_no_scope_file(self):
        """Test stage behavior without scope file"""
        stage = ScopeFilteringStage({}, None)
        
        target = Target(domain='example.com')
        target.subdomains = ['api.example.com', 'test.example.com']
        
        result = stage.execute(target)
        
        self.assertTrue(result)
        # Without scope file, all subdomains should remain
        self.assertEqual(len(target.subdomains), 2)
    
    def test_stage_is_enabled(self):
        """Test is_enabled method"""
        stage_enabled = ScopeFilteringStage({}, self.temp_file.name)
        stage_disabled = ScopeFilteringStage({}, None)
        
        self.assertTrue(stage_enabled.is_enabled())
        self.assertFalse(stage_disabled.is_enabled())


if __name__ == '__main__':
    unittest.main()
