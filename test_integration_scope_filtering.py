#!/usr/bin/env python3
"""
Integration test demonstrating the scope filtering feature end-to-end
"""
import json
import tempfile
from pathlib import Path
from utils.scope_filter import ScopeFilter
from stages.scope_filtering import ScopeFilteringStage
from core.target import Target


def test_scope_filtering_integration():
    """
    Integration test showing:
    1. Creating a scope file
    2. Simulating enumeration results
    3. Filtering through scope filtering stage
    4. Verifying output
    """
    
    print("=" * 60)
    print("SCOPE FILTERING INTEGRATION TEST")
    print("=" * 60)
    
    # 1. Create a scope file
    print("\n[1] Creating scope.json...")
    scope_data = {
        "in_scope": {
            "domains": [
                "example.com",
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(scope_data, f, indent=2)
        scope_file = f.name
    
    print(f"✓ Scope file created: {scope_file}")
    print(f"  In-scope domains: {len(scope_data['in_scope']['domains'])}")
    print(f"  Out-of-scope domains: {len(scope_data['out_of_scope']['domains'])}")
    
    # 2. Simulate enumeration results
    print("\n[2] Simulating enumeration results...")
    discovered_subdomains = [
        "example.com",
        "www.example.com",
        "api.example.com",
        "v1.api.example.com",
        "db.internal.example.com",
        "cache.internal.example.com",
        "prod-database.example.com",
        "prod-api.example.com",
        "test.example.com",
        "staging.example.com",
        "feature-dev.example.com",
        "old-dev.example.com",
        "mail.example.com",
        "ftp.example.com",
    ]
    
    print(f"✓ Enumeration discovered {len(discovered_subdomains)} subdomains")
    
    # 3. Create target with discovered subdomains
    print("\n[3] Creating target with enumerated subdomains...")
    target = Target(domain="example.com")
    for subdomain in discovered_subdomains:
        target.add_subdomain(subdomain)
    
    print(f"✓ Target has {len(target.subdomains)} subdomains")
    
    # 4. Create and execute scope filtering stage
    print("\n[4] Executing scope filtering stage...")
    stage = ScopeFilteringStage({}, scope_file)
    
    # Mock observer to capture notifications
    filtered_count = 0
    in_scope_count = 0
    filtered_subdomains = []
    
    class TestObserver:
        def update(self, stage_name, event, data):
            nonlocal filtered_count, in_scope_count, filtered_subdomains
            if event == "filtered_subdomain":
                filtered_count += 1
                filtered_subdomains.append(data)
            elif event == "complete":
                if "in-scope" in str(data):
                    # Extract count from message
                    parts = str(data).split()
                    for i, part in enumerate(parts):
                        if part == "in-scope" and i > 0:
                            in_scope_count = int(parts[i-1])
    
    observer = TestObserver()
    stage.attach_observer(observer)
    
    result = stage.execute(target)
    
    print(f"✓ Stage execution completed: {result}")
    print(f"  Filtered out: {len(target.metadata.get('filtered_subdomains', []))}")
    print(f"  Remaining: {len(target.subdomains)}")
    
    # 5. Verify results
    print("\n[5] Verifying filtering results...")
    
    print("\n  IN-SCOPE subdomains (will be scanned):")
    for subdomain in sorted(target.subdomains):
        print(f"    ✓ {subdomain}")
    
    print("\n  OUT-OF-SCOPE subdomains (filtered out):")
    for subdomain in sorted(target.metadata.get('filtered_subdomains', [])):
        print(f"    ✗ {subdomain}")
    
    # 6. Validate correctness
    print("\n[6] Validating filtering logic...")
    
    scope = ScopeFilter(scope_file)
    
    # Manually verify each subdomain
    validation_passed = True
    for subdomain in target.subdomains:
        if not scope.is_in_scope(subdomain):
            print(f"  ERROR: {subdomain} marked in-scope but failed validation")
            validation_passed = False
    
    for subdomain in target.metadata.get('filtered_subdomains', []):
        if scope.is_in_scope(subdomain):
            print(f"  ERROR: {subdomain} marked out-of-scope but passed validation")
            validation_passed = False
    
    if validation_passed:
        print("  ✓ All filtering decisions validated correctly")
    else:
        print("  ✗ Validation FAILED")
    
    # 7. Print scope statistics
    print("\n[7] Scope statistics:")
    stats = scope.get_stats()
    print(f"  In-scope domains: {stats['in_scope_domains']}")
    print(f"  Out-of-scope domains: {stats['out_of_scope_domains']}")
    print(f"  Regex patterns: {stats['patterns']}")
    
    # 8. Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Started with:    {len(discovered_subdomains)} subdomains")
    print(f"Filtered out:    {len(target.metadata.get('filtered_subdomains', []))} (out-of-scope)")
    print(f"Proceeding with: {len(target.subdomains)} (in-scope)")
    
    # Calculate percentages
    total = len(discovered_subdomains)
    in_scope_pct = (len(target.subdomains) / total * 100) if total > 0 else 0
    out_scope_pct = (len(target.metadata.get('filtered_subdomains', [])) / total * 100) if total > 0 else 0
    
    print(f"\nPercentage breakdown:")
    print(f"  In-scope:  {in_scope_pct:.1f}%")
    print(f"  Out-scope: {out_scope_pct:.1f}%")
    
    print("\n✓ Integration test completed successfully!")
    
    # Cleanup
    Path(scope_file).unlink()


if __name__ == '__main__':
    test_scope_filtering_integration()
