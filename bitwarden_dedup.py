#!/usr/bin/env python3
"""
Bitwarden Password Deduplication Script

Logic:
- Reads Bitwarden JSON export
- Groups by domain (extracted from login_uri)
- Sorts by revisionDate (newest first)
- Keeps only the newest entry per domain
- Outputs clean JSON for re-import
- Generates report of removed duplicates
"""

import json
import sys
from datetime import datetime
from urllib.parse import urlparse
from collections import defaultdict
from pathlib import Path


def extract_domain(url):
    """Extract domain from URL, handling various formats."""
    if not url:
        return None

    # Handle URLs without protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path

        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]

        return domain.lower()
    except Exception as e:
        print(f"Warning: Could not parse URL '{url}': {e}")
        return None


def parse_date(date_str):
    """Parse ISO 8601 date string to datetime object."""
    if not date_str:
        return datetime.min

    try:
        # Handle both with and without microseconds
        if '.' in date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return datetime.min


def deduplicate_passwords(input_file, output_file=None, report_file=None):
    """
    Deduplicate Bitwarden passwords, keeping newest per domain.

    Args:
        input_file: Path to Bitwarden JSON export
        output_file: Path for clean output (default: input_clean.json)
        report_file: Path for deduplication report (default: dedup_report.txt)
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    # Set default output paths
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}_clean.json"

    if report_file is None:
        report_file = input_path.parent / "dedup_report.txt"

    print(f"Reading {input_file}...")

    # Load Bitwarden JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('items', [])
    print(f"Found {len(items)} total items")

    # Group items by domain
    domain_groups = defaultdict(list)
    no_domain_items = []

    for item in items:
        # Only process login items
        if item.get('type') != 1:  # type 1 = login
            no_domain_items.append(item)
            continue

        # Extract domain from login URIs
        login = item.get('login', {})
        uris = login.get('uris', [])

        if not uris:
            no_domain_items.append(item)
            continue

        # Use first URI's domain
        uri_obj = uris[0]
        uri = uri_obj.get('uri', '')
        domain = extract_domain(uri)

        if domain:
            domain_groups[domain].append(item)
        else:
            no_domain_items.append(item)

    print(f"\nGrouped into {len(domain_groups)} domains")
    print(f"{len(no_domain_items)} items without domains (will be kept)")

    # Deduplicate each domain group
    kept_items = []
    removed_items = []
    dedup_stats = []

    for domain, items_list in sorted(domain_groups.items()):
        if len(items_list) == 1:
            # No duplicates
            kept_items.append(items_list[0])
            continue

        # Sort by revisionDate (newest first)
        items_list.sort(
            key=lambda x: parse_date(x.get('revisionDate', '')),
            reverse=True
        )

        # Keep newest
        newest = items_list[0]
        kept_items.append(newest)

        # Mark rest as removed
        duplicates = items_list[1:]
        removed_items.extend(duplicates)

        # Record stats
        dedup_stats.append({
            'domain': domain,
            'total': len(items_list),
            'kept': newest.get('name', 'Unknown'),
            'kept_date': newest.get('revisionDate', 'Unknown'),
            'removed_count': len(duplicates),
            'removed': [
                {
                    'name': d.get('name', 'Unknown'),
                    'date': d.get('revisionDate', 'Unknown')
                }
                for d in duplicates
            ]
        })

    # Add back non-domain items
    kept_items.extend(no_domain_items)

    # Build clean output
    clean_data = data.copy()
    clean_data['items'] = kept_items

    # Write clean JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Clean vault written to: {output_file}")
    print(f"  - Kept: {len(kept_items)} items")
    print(f"  - Removed: {len(removed_items)} duplicates")

    # Write report
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Bitwarden Deduplication Report\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total items processed: {len(items)}\n")
        f.write(f"Items kept: {len(kept_items)}\n")
        f.write(f"Duplicates removed: {len(removed_items)}\n")
        f.write(f"Domains with duplicates: {len(dedup_stats)}\n\n")
        f.write("=" * 70 + "\n\n")

        if dedup_stats:
            f.write("DEDUPLICATION DETAILS\n\n")

            for stat in dedup_stats:
                f.write(f"Domain: {stat['domain']}\n")
                f.write(f"  Total entries: {stat['total']}\n")
                f.write(f"  KEPT: {stat['kept']} (Updated: {stat['kept_date']})\n")
                f.write(f"  Removed {stat['removed_count']} duplicates:\n")

                for removed in stat['removed']:
                    f.write(f"    - {removed['name']} (Updated: {removed['date']})\n")

                f.write("\n")

    print(f"✓ Report written to: {report_file}")

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Domains with duplicates: {len(dedup_stats)}")

    if dedup_stats:
        # Show top 10 most duplicated domains
        top_dupes = sorted(dedup_stats, key=lambda x: x['removed_count'], reverse=True)[:10]
        print("\nTop 10 most duplicated domains:")
        for i, stat in enumerate(top_dupes, 1):
            print(f"  {i}. {stat['domain']}: {stat['total']} entries ({stat['removed_count']} removed)")

    print(f"\nNext steps:")
    print(f"  1. Review report: {report_file}")
    print(f"  2. Import clean vault: {output_file}")
    print(f"  3. Backup original: {input_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python bitwarden_dedup.py <bitwarden_export.json> [output.json] [report.txt]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    report_file = sys.argv[3] if len(sys.argv) > 3 else None

    deduplicate_passwords(input_file, output_file, report_file)
