from scanners.base_scanner import BaseScanner
from core.target import Vulnerability
from typing import List
from datetime import datetime
import subprocess
import os
import xml.etree.ElementTree as ET
import shutil


class NiktoScanner(BaseScanner):
    """Nikto web server scanner integration"""
    
    def __init__(self, nikto_path: str = None, timeout: int = 300):
        super().__init__("Nikto Scanner")
        self.nikto_path = nikto_path or self._find_nikto()
        self.timeout = timeout
        
        if not self.nikto_path:
            raise FileNotFoundError("Nikto not found. Install: apt-get install nikto")
    
    def _find_nikto(self) -> str:
        """Find Nikto in system PATH"""
        for name in ["nikto", "nikto.pl"]:
            path = shutil.which(name)
            if path:
                return path
        return None
    
    def scan(self, target_url: str) -> List[Vulnerability]:
        """Scan target with Nikto"""
        if not target_url.startswith(('http://', 'https://')):
            target_url = f"https://{target_url}"
        
        # FIX: Validate domain before scanning
        if not self._is_valid_target(target_url):
            print(f"[Nikto] Skipping invalid target: {target_url}")
            return []
        
        vulnerabilities = []
        xml_file = f"/tmp/nikto_{datetime.now().timestamp()}.xml"
        
        try:
            cmd = [self.nikto_path, "-h", target_url, "-o", xml_file, "-Format", "xml"]
            
            print(f"[Nikto] Scanning {target_url}...")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                text=True
            )
            
            if result.returncode != 0 or not os.path.exists(xml_file):
                return []
            
            vulnerabilities = self._parse_xml(xml_file, target_url)
            print(f"[Nikto] Found {len(vulnerabilities)} issues")
            
        except subprocess.TimeoutExpired:
            print(f"[!] Nikto timed out")
        except Exception as e:
            print(f"[!] Nikto error: {e}")
        finally:
            if os.path.exists(xml_file):
                os.remove(xml_file)
        
        return vulnerabilities

    def _is_valid_target(self, url: str) -> bool:
        """Check if target is valid for scanning"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            # Skip if contains invalid characters
            if not hostname or '@' in hostname or ' ' in hostname:
                return False
            
            # Skip certificate transparency artifacts
            if 'test intermediate' in hostname.lower():
                return False
            
            return True
            
        except:
            return False    
        
    def _parse_xml(self, xml_file: str, target_url: str) -> List[Vulnerability]:
        """Parse Nikto XML output to Vulnerability objects"""
        vulnerabilities = []
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            for item in root.findall(".//item"):
                # Extract data
                desc = item.findtext("description", "Nikto finding")
                uri = item.findtext("uri", "")
                osvdb = item.findtext("osvdbid", "")
                
                # Map severity (Nikto doesn't provide severity, use 'medium' default)
                severity = "medium"
                
                # Create vulnerability
                vuln = Vulnerability(
                    vuln_type="nikto_finding",
                    severity=severity,
                    url=f"{target_url}{uri}",
                    parameter="N/A",
                    payload="N/A",
                    evidence=f"Description: {desc} | OSVDB: {osvdb}",
                    timestamp=datetime.now()
                )
                
                vulnerabilities.append(vuln)
                
        except Exception as e:
            print(f"[!] XML parse error: {e}")
        
        return vulnerabilities