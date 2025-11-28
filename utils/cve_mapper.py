"""
CVE Mapping Utility using NIST NVD API

Maps discovered vulnerabilities to known CVEs using the NIST National Vulnerability Database.
This provides real, authoritative CVE data instead of static patterns.
"""

from typing import Dict, List, Optional
from core.target import Vulnerability
import requests
import json
from datetime import datetime, timedelta
import logging


class CVEMapper:
    """Maps vulnerabilities to known CVEs using NIST NVD API"""
    
    # NIST NVD API endpoints
    NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # Cache to avoid repeated API calls
    _cache: Dict[str, Dict] = {}
    _cache_expiry: Dict[str, datetime] = {}
    CACHE_DURATION = 3600  # 1 hour
    
    logger = logging.getLogger(__name__)
    
    @classmethod
    def search_cve_by_keyword(cls, keyword: str, severity: Optional[str] = None) -> List[Dict]:
        """
        Search NIST NVD for CVEs matching a keyword
        
        Args:
            keyword: Search keyword (e.g., 'SQL injection', 'Microsoft SQL Server')
            severity: Optional severity filter ('critical', 'high', 'medium', 'low')
            
        Returns:
            List of matching CVE records
        """
        # Check cache first
        cache_key = f"{keyword}:{severity}"
        if cache_key in cls._cache:
            if cls._cache_expiry.get(cache_key, datetime.now()) > datetime.now():
                return cls._cache[cache_key]
        
        try:
            # Query NIST NVD API
            params = {
                'keywordSearch': keyword,
                'resultsPerPage': 20
            }
            
            response = requests.get(
                cls.NVD_API_BASE,
                params=params,
                timeout=10,
                headers={'User-Agent': 'GrayTera/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get('vulnerabilities', [])
                
                # Don't filter by severity - NIST API may return CVEs without severity info
                # in the response, severity filtering should happen at display time
                
                # Cache the results
                cls._cache[cache_key] = vulnerabilities
                cls._cache_expiry[cache_key] = datetime.now() + timedelta(seconds=cls.CACHE_DURATION)
                
                return vulnerabilities
            else:
                cls.logger.warning(f"NIST API returned status {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            cls.logger.debug(f"Failed to query NIST API: {e}")
            return []
        except json.JSONDecodeError as e:
            cls.logger.debug(f"Failed to parse NIST API response: {e}")
            return []
    
    @classmethod
    def map_to_cve(cls, vuln: Vulnerability) -> Optional[Dict]:
        """
        Attempt to map a vulnerability to known CVEs via NIST API
        
        Args:
            vuln: Vulnerability object to map
            
        Returns:
            Dict with CVE info if found, None otherwise
        """
        # Build search query based on vulnerability type and evidence
        search_queries = cls._build_search_queries(vuln)
        
        best_match = None
        
        for query in search_queries:
            results = cls.search_cve_by_keyword(query, severity=vuln.severity)
            
            if results:
                # Take the first (most relevant) result
                best_match = cls._parse_cve_record(results[0])
                break
        
        return best_match
    
    @classmethod
    def _build_search_queries(cls, vuln: Vulnerability) -> List[str]:
        """Build ordered list of search queries based on vulnerability type"""
        queries = []
        vuln_type = vuln.vuln_type.lower()
        evidence = vuln.evidence.lower()
        
        # Type-specific queries
        if vuln_type == 'sqli':
            if 'microsoft sql server' in evidence or 'mssql' in evidence:
                queries.append('SQL injection Microsoft SQL Server')
            elif 'postgresql' in evidence:
                queries.append('SQL injection PostgreSQL')
            elif 'mysql' in evidence:
                queries.append('SQL injection MySQL')
            else:
                queries.append('SQL injection database')
        
        elif vuln_type == 'xss':
            queries.append('Cross Site Scripting XSS')
        
        elif vuln_type == 'csrf':
            queries.append('Cross Site Request Forgery CSRF')
        
        elif vuln_type == 'rfi':
            queries.append('Remote File Inclusion RFI')
        
        elif vuln_type == 'lfi':
            queries.append('Local File Inclusion LFI')
        
        elif vuln_type == 'command_injection':
            queries.append('Command injection')
        
        # Fallback generic query
        if not queries:
            queries.append(f'{vuln_type} vulnerability')
        
        return queries
    
    @classmethod
    def _parse_cve_record(cls, cve_record: Dict) -> Optional[Dict]:
        """Parse NIST NVD CVE record into standard format"""
        try:
            cve = cve_record.get('cve', {})
            cve_id = cve.get('id')
            
            # Extract description
            descriptions = cve.get('descriptions', [])
            description = descriptions[0].get('value', '') if descriptions else ''
            
            # Extract severity and CVSS score
            # The metrics might not always be present
            metrics = cve.get('metrics', {})
            cvss_v3 = (metrics.get('cvssV3') or [{}])[0] if metrics.get('cvssV3') else {}
            severity = cvss_v3.get('baseSeverity', 'UNKNOWN').lower()
            score = cvss_v3.get('baseScore', 0)
            
            # Fallback to cvssV2 if V3 not available
            if severity == 'unknown':
                cvss_v2 = (metrics.get('cvssV2') or [{}])[0] if metrics.get('cvssV2') else {}
                severity = cvss_v2.get('baseSeverity', 'UNKNOWN').lower()
                score = cvss_v2.get('baseScore', 0)
            
            # Extract published date
            published = cve.get('published', '')
            
            return {
                'id': cve_id,
                'description': description,
                'severity': severity,
                'score': score,
                'published': published,
                'source': 'NIST NVD'
            }
        except (KeyError, IndexError, TypeError) as e:
            return None
    
    @classmethod
    def _extract_severity(cls, cve_record: Dict) -> str:
        """Extract severity from NIST CVE record"""
        try:
            metrics = cve_record.get('cve', {}).get('metrics', {})
            cvss_v3 = metrics.get('cvssV3', [{}])[0]
            return cvss_v3.get('baseSeverity', 'UNKNOWN')
        except (KeyError, IndexError, TypeError):
            return 'UNKNOWN'
    
    @classmethod
    def enrich_vulnerabilities(cls, vulnerabilities: List[Vulnerability]) -> List[Vulnerability]:
        """
        Enrich a list of vulnerabilities with CVE information from NIST
        
        Args:
            vulnerabilities: List of Vulnerability objects
            
        Returns:
            Same list with cve_id fields populated where applicable
        """
        for vuln in vulnerabilities:
            if not vuln.cve_id:
                cve_info = cls.map_to_cve(vuln)
                if cve_info:
                    vuln.cve_id = cve_info.get('id')
                    # Store full CVE info in metadata for later use
                    if not hasattr(vuln, 'cve_info'):
                        vuln.cve_info = cve_info
        
        return vulnerabilities
    
    @classmethod
    def get_cve_summary(cls, vulnerabilities: List[Vulnerability]) -> Dict:
        """
        Get summary of CVEs found in vulnerabilities
        
        Returns:
            Dict with CVE statistics
        """
        cve_counts = {}
        uncategorized = 0
        
        for vuln in vulnerabilities:
            if vuln.cve_id:
                cve_counts[vuln.cve_id] = cve_counts.get(vuln.cve_id, 0) + 1
            else:
                uncategorized += 1
        
        return {
            'total_vulns': len(vulnerabilities),
            'identified_cves': len(cve_counts),
            'uncategorized': uncategorized,
            'cve_breakdown': cve_counts
        }
    
    @classmethod
    def deduplicate_by_cve(cls, vulnerabilities: List[Vulnerability]) -> Dict[str, Dict]:
        """
        Group vulnerabilities by CVE ID and consolidate findings
        
        Consolidates multiple findings of the same CVE with tracking of:
        - All affected parameters/endpoints
        - Payloads that successfully exploited it
        - Number of times vulnerability was discovered
        
        Args:
            vulnerabilities: List of Vulnerability objects
            
        Returns:
            Dict mapping CVE ID to consolidated finding info:
            {
                'CVE-XXXX-XXXXX': {
                    'vuln_type': 'sqli',
                    'severity': 'high',
                    'url': 'http://example.com',
                    'cve_id': 'CVE-XXXX-XXXXX',
                    'affected_parameters': [
                        {'url': 'http://example.com', 'parameter': 'id', 'payloads': [...]},
                        {'url': 'http://example.com', 'parameter': 'search', 'payloads': [...]}
                    ],
                    'count': 2,
                    'timestamps': [datetime, datetime]
                },
                ...
            }
        """
        cve_map: Dict[str, Dict] = {}
        
        for vuln in vulnerabilities:
            cve_id = vuln.cve_id or 'UNCATEGORIZED'
            
            if cve_id not in cve_map:
                cve_map[cve_id] = {
                    'vuln_type': vuln.vuln_type,
                    'severity': vuln.severity,
                    'url': vuln.url,
                    'cve_id': cve_id,
                    'evidence': vuln.evidence,
                    'affected_parameters': [],
                    'count': 0,
                    'timestamps': []
                }
            
            # Track affected parameters and payloads
            param_entry = None
            for entry in cve_map[cve_id]['affected_parameters']:
                if entry['url'] == vuln.url and entry['parameter'] == vuln.parameter:
                    param_entry = entry
                    break
            
            if param_entry is None:
                param_entry = {
                    'url': vuln.url,
                    'parameter': vuln.parameter,
                    'payloads': []
                }
                cve_map[cve_id]['affected_parameters'].append(param_entry)
            
            # Add payload if not already recorded
            if vuln.payload not in param_entry['payloads']:
                param_entry['payloads'].append(vuln.payload)
            
            # Update counters
            cve_map[cve_id]['count'] += 1
            cve_map[cve_id]['timestamps'].append(vuln.timestamp)
        
        return cve_map
    
    @classmethod
    def clear_cache(cls):
        """Clear CVE cache"""
        cls._cache.clear()
        cls._cache_expiry.clear()


# Example usage function
def analyze_vulnerabilities_for_cves(vulnerabilities: List[Vulnerability]) -> Dict:
    """
    Analyze vulnerabilities and provide CVE insights using NIST API
    
    Args:
        vulnerabilities: List of discovered vulnerabilities
        
    Returns:
        Analysis results with CVE information
    """
    # Enrich with CVE data from NIST
    enriched = CVEMapper.enrich_vulnerabilities(vulnerabilities)
    
    # Get summary
    summary = CVEMapper.get_cve_summary(enriched)
    
    return {
        'vulnerabilities': enriched,
        'summary': summary
    }

