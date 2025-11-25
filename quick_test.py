import sys
from core.target import Vulnerability
from exploits.sqli_exploit import SQLiExploit
from datetime import datetime
import yaml

url = sys.argv[1] if len(sys.argv) > 1 else input("Enter URL: ")
with open('config.yaml') as f:
    config = yaml.safe_load(f).get('exploitation', {})
vuln = Vulnerability('sqli', 'high', url, '', '', 'CLI test', datetime.now())
result = SQLiExploit(config).execute(vuln)
print(f"\n{'='*70}\nSuccess: {result['success']}\nTime: {result['time_elapsed']:.1f}s\n{'='*70}\n{result['evidence']}")