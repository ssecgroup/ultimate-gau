"""
Command-line interface for Ultimate GAU
"""

import argparse
import sys
from .core import UltimateGAU

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Ultimate GAU - Get All URLs from multiple free sources",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add all your existing arguments
    parser.add_argument("domain", nargs="?", help="Target domain")
    parser.add_argument("--subs", "-s", action="store_true", help="Include subdomains")
    parser.add_argument("--providers", "-p", help="Comma-separated providers")
    parser.add_argument("--all", "-a", action="store_true", help="Use all providers")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--format", "-f", choices=['txt', 'json', 'csv'], default='txt')
    parser.add_argument("--silent", "-q", action="store_true", help="Silent mode")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--threads", "-t", type=int, default=5, help="Number of threads")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout")
    parser.add_argument("--match", "-m", help="Regex pattern to include")
    parser.add_argument("--exclude", "-e", help="Regex pattern to exclude")
    parser.add_argument("--include-ext", help="Extensions to include")
    parser.add_argument("--exclude-ext", help="Extensions to exclude")
    parser.add_argument("--cache", action="store_true", help="Enable caching")
    parser.add_argument("--cache-duration", type=int, default=86400, help="Cache duration")
    parser.add_argument("--rate-limit", type=int, default=10, help="Rate limit per second")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--stdin", action="store_true", help="Read domains from stdin")
    parser.add_argument("--list-providers", action="store_true", help="List providers")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache")
    parser.add_argument("--version", action="store_true", help="Show version")
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.version:
        from . import __version__
        print(f"Ultimate GAU v{__version__}")
        return
    
    if args.list_providers:
        from .core import UltimateGAU
        print("\nAvailable providers:")
        for key, name in UltimateGAU.PROVIDERS.items():
            print(f"  {key:15} - {name}")
        return
    
    # Rest of your main function logic
    # ...
