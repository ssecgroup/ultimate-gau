#!/usr/bin/env python3
"""
Custom GAU (Get All URLs) - Ultimate Edition
Fetch archived URLs from multiple free sources
Inspired by: https://github.com/lc/gau
"""

import argparse
import json
import requests
import sys
import time
import re
import os
import hashlib
import pickle
import socket
import gzip
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
from collections import Counter
from pathlib import Path
from typing import Set, List, Dict, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Optional imports for enhanced features
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    import validators
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False


@dataclass
class URLData:
    """Data class for URL metadata"""
    url: str
    scheme: str
    domain: str
    path: str
    query: str
    fragment: str
    file_extension: str
    parameter_count: int
    source: str
    timestamp: str = ""


class RateLimiter:
    """Simple rate limiter for API requests"""
    def __init__(self, max_calls: int = 10, period: int = 1):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        # Remove old calls
        self.calls = [t for t in self.calls if t > now - self.period]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.period - now
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.calls.append(now)


class CacheManager:
    """Manage caching of results"""
    def __init__(self, cache_dir: str = ".gau_cache"):
        self.cache_dir = Path.home() / cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, domain: str, provider: str, subs: bool) -> str:
        """Generate cache key"""
        key_string = f"{domain}_{provider}_{subs}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, domain: str, provider: str, subs: bool, max_age: int = 86400) -> Optional[Set[str]]:
        """Get cached results if fresh"""
        cache_key = self._get_cache_key(domain, provider, subs)
        cache_file = self.cache_dir / cache_key
        
        if cache_file.exists():
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < max_age:
                try:
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
                except:
                    pass
        return None
    
    def set(self, domain: str, provider: str, subs: bool, urls: Set[str]):
        """Cache results"""
        cache_key = self._get_cache_key(domain, provider, subs)
        cache_file = self.cache_dir / cache_key
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(urls, f)
        except:
            pass


class UltimateGAU:
    """Ultimate GAU - Get All URLs from multiple sources"""
    
    # Available providers (all free, no API keys required)
    PROVIDERS = {
        'wayback': 'Wayback Machine',
        'otx': 'AlienVault OTX',
        'commoncrawl': 'Common Crawl',
        'ukwa': 'UK Web Archive',
        'arquivo': 'Arquivo.pt',
        'libraryofcongress': 'Library of Congress',
        'stanford': 'Stanford Web Archive',
        'archiveit': 'Archive-It',
        'parliamentuk': 'UK Parliament Web Archive'
    }
    
    def __init__(self, 
                 domain: str,
                 subs: bool = True,
                 providers: List[str] = None,
                 threads: int = 5,
                 timeout: int = 30,
                 match_pattern: str = None,
                 exclude_pattern: str = None,
                 include_extensions: List[str] = None,
                 exclude_extensions: List[str] = None,
                 min_length: int = 1,
                 max_length: int = 2000,
                 use_cache: bool = True,
                 cache_duration: int = 86400,
                 rate_limit: int = 10,
                 silent: bool = False,
                 json_output: bool = False,
                 verbose: bool = False):
        
        self.domain = domain.lower().strip()
        self.subs = subs
        self.providers = providers or list(self.PROVIDERS.keys())
        self.threads = threads
        self.timeout = timeout
        self.match_pattern = re.compile(match_pattern) if match_pattern else None
        self.exclude_pattern = re.compile(exclude_pattern) if exclude_pattern else None
        self.include_extensions = set(ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                                     for ext in (include_extensions or []))
        self.exclude_extensions = set(ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                                     for ext in (exclude_extensions or ['.css', '.js', '.jpg', '.jpeg', 
                                                                       '.png', '.gif', '.ico', '.svg', 
                                                                       '.woff', '.woff2', '.ttf', '.eot']))
        self.min_length = min_length
        self.max_length = max_length
        self.use_cache = use_cache
        self.cache_duration = cache_duration
        self.rate_limiter = RateLimiter(max_calls=rate_limit)
        self.silent = silent
        self.json_output = json_output
        self.verbose = verbose
        
        # Initialize components
        self.cache = CacheManager() if use_cache else None
        self.session = self._create_session()
        self.results: Set[str] = set()
        self.enriched_results: List[URLData] = []
        self.provider_stats: Dict[str, int] = {}
        self.start_time = None
        self.end_time = None
    
    def _create_session(self) -> requests.Session:
        """Create optimized session"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; UltimateGAU/3.0; +https://github.com/ultimate-gau)',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        })
        
        # Configure retries
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=2
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def _log(self, message: str, level: str = "info"):
        """Log message based on verbosity settings"""
        if self.silent:
            return
        
        if level == "error":
            print(f"[-] {message}", file=sys.stderr)
        elif level == "warning":
            print(f"[!] {message}", file=sys.stderr)
        elif level == "success":
            print(f"[+] {message}", file=sys.stderr)
        elif level == "debug" and self.verbose:
            print(f"[*] {message}", file=sys.stderr)
        elif level == "info" and not self.silent:
            print(f"[*] {message}", file=sys.stderr)
    
    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and normalize URL"""
        if not url or not isinstance(url, str):
            return None
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        try:
            parsed = urlparse(url)
            
            # Apply length filters
            if len(url) < self.min_length or len(url) > self.max_length:
                return None
            
            # Check domain
            domain = parsed.netloc.lower()
            if self.subs:
                if not (domain == self.domain or domain.endswith('.' + self.domain)):
                    return None
            else:
                if domain != self.domain:
                    return None
            
            # Remove fragments
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Sort query parameters
            if parsed.query:
                params = parse_qs(parsed.query, keep_blank_values=True)
                sorted_params = sorted(params.items())
                query_string = '&'.join([f"{k}={v[0]}" if v[0] != '' else k 
                                       for k, v in sorted_params])
                if query_string:
                    clean_url += f"?{query_string}"
            
            # Apply regex filters
            if self.match_pattern and not self.match_pattern.search(clean_url):
                return None
            
            if self.exclude_pattern and self.exclude_pattern.search(clean_url):
                return None
            
            # Check file extension
            ext = os.path.splitext(parsed.path)[1].lower()
            if self.include_extensions and ext not in self.include_extensions:
                return None
            if self.exclude_extensions and ext in self.exclude_extensions:
                return None
            
            # Validate URL if validators available
            if VALIDATORS_AVAILABLE and not validators.url(clean_url):
                return None
            
            return clean_url
            
        except Exception as e:
            if self.verbose:
                self._log(f"URL cleaning error: {e}", "debug")
            return None
    
    def _fetch_with_retry(self, url: str, params: dict = None, timeout: int = None) -> Optional[requests.Response]:
        """Fetch URL with rate limiting and retry"""
        self.rate_limiter.wait_if_needed()
        
        for attempt in range(2):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=timeout or self.timeout,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too Many Requests
                    time.sleep(2 ** attempt)
                else:
                    return None
                    
            except Exception as e:
                if attempt == 1:
                    self._log(f"Request failed: {e}", "debug")
                time.sleep(1)
        
        return None
    
    # Provider implementations
    def fetch_wayback(self) -> Set[str]:
        """Fetch from Wayback Machine"""
        urls = set()
        provider = "wayback"
        
        # Check cache
        if self.cache:
            cached = self.cache.get(self.domain, provider, self.subs, self.cache_duration)
            if cached is not None:
                self.provider_stats[provider] = len(cached)
                self._log(f"Wayback Machine (cached): {len(cached)} URLs", "success")
                return cached
        
        try:
            base_url = "http://web.archive.org/cdx/search/cdx"
            params = {
                'url': f"*.{self.domain}/*" if self.subs else f"{self.domain}/*",
                'output': 'json',
                'fl': 'original',
                'collapse': 'urlkey',
                'limit': '150000'
            }
            
            response = self._fetch_with_retry(base_url, params=params, timeout=self.timeout * 2)
            if response:
                data = response.json()
                if len(data) > 1:
                    for item in data[1:]:
                        if item and len(item) > 0:
                            clean_url = self._clean_url(item[0])
                            if clean_url:
                                urls.add(clean_url)
            
            # Cache results
            if self.cache and urls:
                self.cache.set(self.domain, provider, self.subs, urls)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"Wayback Machine: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"Wayback Machine error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def fetch_otx(self) -> Set[str]:
        """Fetch from AlienVault OTX"""
        urls = set()
        provider = "otx"
        
        if self.cache:
            cached = self.cache.get(self.domain, provider, self.subs, self.cache_duration)
            if cached is not None:
                self.provider_stats[provider] = len(cached)
                self._log(f"AlienVault OTX (cached): {len(cached)} URLs", "success")
                return cached
        
        try:
            base_url = f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/url_list"
            params = {'limit': 500, 'page': 1}
            
            while True:
                response = self._fetch_with_retry(base_url, params=params)
                if not response:
                    break
                
                data = response.json()
                for item in data.get('url_list', []):
                    url = item.get('url', '')
                    clean_url = self._clean_url(url)
                    if clean_url:
                        urls.add(clean_url)
                
                if not data.get('has_next'):
                    break
                params['page'] += 1
            
            if self.cache and urls:
                self.cache.set(self.domain, provider, self.subs, urls)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"AlienVault OTX: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"OTX error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def fetch_commoncrawl(self) -> Set[str]:
        """Fetch from Common Crawl"""
        urls = set()
        provider = "commoncrawl"
        
        if self.cache:
            cached = self.cache.get(self.domain, provider, self.subs, self.cache_duration)
            if cached is not None:
                self.provider_stats[provider] = len(cached)
                self._log(f"Common Crawl (cached): {len(cached)} URLs", "success")
                return cached
        
        try:
            # Get indexes
            index_url = "https://index.commoncrawl.org/collinfo.json"
            response = self._fetch_with_retry(index_url)
            if not response:
                return urls
            
            indexes = response.json()
            for idx in indexes[:2]:  # Use last 2 indexes
                crawl_id = idx['id']
                
                cc_url = f"https://index.commoncrawl.org/{crawl_id}-cdx"
                params = {
                    'url': f"*.{self.domain}/*" if self.subs else f"{self.domain}/*",
                    'output': 'json',
                    'limit': '50000'
                }
                
                response = self._fetch_with_retry(cc_url, params=params, timeout=self.timeout * 3)
                if response:
                    for line in response.text.strip().split('\n'):
                        if line:
                            try:
                                data = json.loads(line)
                                if 'url' in data:
                                    clean_url = self._clean_url(data['url'])
                                    if clean_url:
                                        urls.add(clean_url)
                            except:
                                continue
            
            if self.cache and urls:
                self.cache.set(self.domain, provider, self.subs, urls)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"Common Crawl: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"Common Crawl error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def fetch_ukwa(self) -> Set[str]:
        """Fetch from UK Web Archive"""
        urls = set()
        provider = "ukwa"
        
        if self.cache:
            cached = self.cache.get(self.domain, provider, self.subs, self.cache_duration)
            if cached is not None:
                self.provider_stats[provider] = len(cached)
                self._log(f"UK Web Archive (cached): {len(cached)} URLs", "success")
                return cached
        
        try:
            base_url = "https://www.webarchive.org.uk/wayback/archive/cdx/search/cdx"
            params = {
                'url': f"*.{self.domain}/*" if self.subs else f"{self.domain}/*",
                'output': 'json',
                'fl': 'original',
                'limit': '50000'
            }
            
            response = self._fetch_with_retry(base_url, params=params)
            if response:
                data = response.json()
                if len(data) > 1:
                    for item in data[1:]:
                        if item and len(item) > 0:
                            clean_url = self._clean_url(item[0])
                            if clean_url:
                                urls.add(clean_url)
            
            if self.cache and urls:
                self.cache.set(self.domain, provider, self.subs, urls)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"UK Web Archive: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"UK Web Archive error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def fetch_arquivo(self) -> Set[str]:
        """Fetch from Arquivo.pt"""
        urls = set()
        provider = "arquivo"
        
        if self.cache:
            cached = self.cache.get(self.domain, provider, self.subs, self.cache_duration)
            if cached is not None:
                self.provider_stats[provider] = len(cached)
                self._log(f"Arquivo.pt (cached): {len(cached)} URLs", "success")
                return cached
        
        try:
            base_url = "https://arquivo.pt/wayback/cdx/search/cdx"
            params = {
                'url': f"*.{self.domain}/*" if self.subs else f"{self.domain}/*",
                'output': 'json',
                'fl': 'original',
                'limit': '50000'
            }
            
            response = self._fetch_with_retry(base_url, params=params)
            if response:
                data = response.json()
                if len(data) > 1:
                    for item in data[1:]:
                        if item and len(item) > 0:
                            clean_url = self._clean_url(item[0])
                            if clean_url:
                                urls.add(clean_url)
            
            if self.cache and urls:
                self.cache.set(self.domain, provider, self.subs, urls)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"Arquivo.pt: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"Arquivo.pt error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def fetch_libraryofcongress(self) -> Set[str]:
        """Fetch from Library of Congress Web Archive"""
        urls = set()
        provider = "libraryofcongress"
        
        try:
            base_url = "https://webarchive.loc.gov/all/cdx/search/cdx"
            params = {
                'url': f"*.{self.domain}/*" if self.subs else f"{self.domain}/*",
                'output': 'json',
                'fl': 'original',
                'limit': '50000'
            }
            
            response = self._fetch_with_retry(base_url, params=params)
            if response:
                data = response.json()
                if len(data) > 1:
                    for item in data[1:]:
                        if item and len(item) > 0:
                            clean_url = self._clean_url(item[0])
                            if clean_url:
                                urls.add(clean_url)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"Library of Congress: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"Library of Congress error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def fetch_stanford(self) -> Set[str]:
        """Fetch from Stanford Web Archive"""
        urls = set()
        provider = "stanford"
        
        try:
            base_url = "https://swap.stanford.edu/cdx/search/cdx"
            params = {
                'url': f"*.{self.domain}/*" if self.subs else f"{self.domain}/*",
                'output': 'json',
                'fl': 'original',
                'limit': '50000'
            }
            
            response = self._fetch_with_retry(base_url, params=params)
            if response:
                data = response.json()
                if len(data) > 1:
                    for item in data[1:]:
                        if item and len(item) > 0:
                            clean_url = self._clean_url(item[0])
                            if clean_url:
                                urls.add(clean_url)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"Stanford Web Archive: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"Stanford error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def fetch_archiveit(self) -> Set[str]:
        """Fetch from Archive-It"""
        urls = set()
        provider = "archiveit"
        
        try:
            base_url = "https://wayback.archive-it.org/cdx/search/cdx"
            params = {
                'url': f"*.{self.domain}/*" if self.subs else f"{self.domain}/*",
                'output': 'json',
                'fl': 'original',
                'limit': '50000'
            }
            
            response = self._fetch_with_retry(base_url, params=params)
            if response:
                data = response.json()
                if len(data) > 1:
                    for item in data[1:]:
                        if item and len(item) > 0:
                            clean_url = self._clean_url(item[0])
                            if clean_url:
                                urls.add(clean_url)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"Archive-It: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"Archive-It error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def fetch_parliamentuk(self) -> Set[str]:
        """Fetch from UK Parliament Web Archive"""
        urls = set()
        provider = "parliamentuk"
        
        try:
            base_url = "https://webarchive.parliament.uk/cdx/search/cdx"
            params = {
                'url': f"*.{self.domain}/*" if self.subs else f"{self.domain}/*",
                'output': 'json',
                'fl': 'original',
                'limit': '50000'
            }
            
            response = self._fetch_with_retry(base_url, params=params)
            if response:
                data = response.json()
                if len(data) > 1:
                    for item in data[1:]:
                        if item and len(item) > 0:
                            clean_url = self._clean_url(item[0])
                            if clean_url:
                                urls.add(clean_url)
            
            self.provider_stats[provider] = len(urls)
            self._log(f"UK Parliament Archive: {len(urls)} URLs", "success")
            
        except Exception as e:
            self._log(f"UK Parliament error: {e}", "error")
            self.provider_stats[provider] = 0
        
        return urls
    
    def enrich_urls(self, urls: Set[str]) -> List[URLData]:
        """Add metadata to URLs"""
        enriched = []
        
        for url in urls:
            parsed = urlparse(url)
            ext = os.path.splitext(parsed.path)[1]
            
            url_data = URLData(
                url=url,
                scheme=parsed.scheme,
                domain=parsed.netloc,
                path=parsed.path,
                query=parsed.query,
                fragment=parsed.fragment,
                file_extension=ext,
                parameter_count=len(parse_qs(parsed.query)) if parsed.query else 0,
                source="gau",
                timestamp=datetime.now().isoformat()
            )
            enriched.append(url_data)
        
        return enriched
    
    def run(self) -> Set[str]:
        """Run all providers and collect URLs"""
        self.start_time = time.time()
        all_urls = set()
        
        # Provider mapping
        provider_functions = {
            'wayback': self.fetch_wayback,
            'otx': self.fetch_otx,
            'commoncrawl': self.fetch_commoncrawl,
            'ukwa': self.fetch_ukwa,
            'arquivo': self.fetch_arquivo,
            'libraryofcongress': self.fetch_libraryofcongress,
            'stanford': self.fetch_stanford,
            'archiveit': self.fetch_archiveit,
            'parliamentuk': self.fetch_parliamentuk
        }
        
        # Filter to requested providers
        active_providers = [p for p in self.providers if p in provider_functions]
        
        if not active_providers:
            self._log("No valid providers specified", "error")
            return all_urls
        
        self._log(f"Starting scan for {self.domain}", "info")
        self._log(f"Providers: {', '.join(active_providers)}", "info")
        
        # Run providers concurrently
        if TQDM_AVAILABLE and not self.silent:
            pbar = tqdm(total=len(active_providers), desc="Fetching", unit="provider")
        
        with ThreadPoolExecutor(max_workers=min(self.threads, len(active_providers))) as executor:
            future_to_provider = {
                executor.submit(provider_functions[p]): p 
                for p in active_providers
            }
            
            for future in as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    urls = future.result(timeout=self.timeout * 2)
                    all_urls.update(urls)
                    
                    if TQDM_AVAILABLE and not self.silent:
                        pbar.update(1)
                        pbar.set_description(f"✓ {provider}: {len(urls)} URLs")
                    else:
                        self._log(f"Completed {provider}", "success")
                        
                except Exception as e:
                    self._log(f"{provider} failed: {e}", "error")
                    if TQDM_AVAILABLE and not self.silent:
                        pbar.update(1)
                        pbar.set_description(f"✗ {provider}")
        
        if TQDM_AVAILABLE and not self.silent:
            pbar.close()
        
        # Enrich URLs
        self.enriched_results = self.enrich_urls(all_urls)
        
        self.end_time = time.time()
        self.results = all_urls
        
        # Final summary
        if not self.silent:
            elapsed = self.end_time - self.start_time
            self._log(f"Scan completed in {elapsed:.2f}s", "success")
            self._log(f"Total unique URLs: {len(all_urls)}", "success")
            
            if self.verbose:
                for provider, count in self.provider_stats.items():
                    if count > 0:
                        self._log(f"  {self.PROVIDERS.get(provider, provider)}: {count}", "debug")
        
        return all_urls
    
    def get_statistics(self) -> Dict:
        """Generate comprehensive statistics"""
        if not self.results:
            return {}
        
        domains = []
        extensions = []
        schemes = []
        param_counts = []
        
        for url_data in self.enriched_results:
            domains.append(url_data.domain)
            if url_data.file_extension:
                extensions.append(url_data.file_extension)
            schemes.append(url_data.scheme)
            param_counts.append(url_data.parameter_count)
        
        stats = {
            'scan_info': {
                'domain': self.domain,
                'subdomains': self.subs,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'duration': self.end_time - self.start_time if self.end_time else 0
            },
            'urls': {
                'total': len(self.results),
                'unique_domains': len(set(domains)),
                'domains': list(set(domains)),
                'schemes': dict(Counter(schemes)),
                'file_extensions': dict(Counter(extensions).most_common(20)),
                'parameterized_urls': sum(1 for c in param_counts if c > 0),
                'total_parameters': sum(param_counts)
            },
            'providers': self.provider_stats,
            'filters': {
                'match_pattern': str(self.match_pattern.pattern) if self.match_pattern else None,
                'exclude_pattern': str(self.exclude_pattern.pattern) if self.exclude_pattern else None,
                'include_extensions': list(self.include_extensions) if self.include_extensions else None,
                'exclude_extensions': list(self.exclude_extensions)
            }
        }
        
        return stats
    
    def output_json(self, output_file=None):
        """Output results in JSON format"""
        output_data = {
            'metadata': {
                'tool': 'UltimateGAU',
                'version': '3.0',
                'timestamp': datetime.now().isoformat(),
                'command': ' '.join(sys.argv)
            },
            'statistics': self.get_statistics(),
            'urls': [asdict(url_data) for url_data in self.enriched_results]
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
        else:
            json.dump(output_data, sys.stdout, indent=2)
            print()
    
    def output_text(self, output_file=None):
        """Output results in text format"""
        handle = open(output_file, 'w') if output_file else sys.stdout
        
        try:
            for url in sorted(self.results):
                handle.write(url + '\n')
        finally:
            if output_file:
                handle.close()
    
    def output_csv(self, output_file):
        """Output results in CSV format"""
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'scheme', 'domain', 'path', 'query', 
                           'fragment', 'extension', 'parameters'])
            
            for url_data in self.enriched_results:
                writer.writerow([
                    url_data.url,
                    url_data.scheme,
                    url_data.domain,
                    url_data.path,
                    url_data.query,
                    url_data.fragment,
                    url_data.file_extension,
                    url_data.parameter_count
                ])


def main():
    parser = argparse.ArgumentParser(
        description="""
╔════════════════════════════════════════════════════════════════╗
║                    Ultimate GAU - Get All URLs                 ║
║         Fetch archived URLs from multiple free sources         ║
╚════════════════════════════════════════════════════════════════╝
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  ugau example.com
  
  # Include subdomains, output to file
  ugau example.com --subs --output urls.txt
  
  # Use specific providers
  ugau example.com --providers wayback,otx,commoncrawl
  
  # Silent mode with JSON output
  ugau example.com --subs --all --silent --json > results.json
  
  # Advanced filtering
  ugau example.com --subs --match "api|admin" --exclude "\.css|\.png" --verbose
  
  # Read from stdin
  cat domains.txt | ugau --stdin --subs --output all_urls.txt
  
  # Get statistics only
  ugau example.com --subs --stats --verbose
  
  # Cache results for 24 hours
  ugau example.com --subs --cache --cache-duration 86400
  
  # Rate limited scanning
  ugau example.com --rate-limit 5 --threads 3

Providers (all free):
  wayback         - Wayback Machine
  otx             - AlienVault OTX
  commoncrawl     - Common Crawl
  ukwa            - UK Web Archive
  arquivo         - Arquivo.pt
  libraryofcongress - Library of Congress
  stanford        - Stanford Web Archive
  archiveit       - Archive-It
  parliamentuk    - UK Parliament Web Archive
        """
    )
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_group.add_argument("domain", nargs="?", help="Target domain (e.g., example.com)")
    input_group.add_argument("--stdin", action="store_true", help="Read domains from stdin")
    
    # Provider options
    provider_group = parser.add_argument_group('Provider Options')
    provider_group.add_argument("--providers", "-p", 
                               help="Comma-separated providers (use --list-providers to see all)")
    provider_group.add_argument("--all", "-a", action="store_true", 
                               help="Use all available providers")
    provider_group.add_argument("--list-providers", action="store_true", 
                               help="List all available providers and exit")
    
    # Scan options
    scan_group = parser.add_argument_group('Scan Options')
    scan_group.add_argument("--subs", "-s", action="store_true", help="Include subdomains")
    scan_group.add_argument("--threads", "-t", type=int, default=5, 
                           help="Number of threads (default: 5)")
    scan_group.add_argument("--timeout", type=int, default=30, 
                           help="Request timeout in seconds (default: 30)")
    scan_group.add_argument("--rate-limit", type=int, default=10, 
                           help="Max requests per second (default: 10)")
    
    # Filter options
    filter_group = parser.add_argument_group('Filter Options')
    filter_group.add_argument("--match", "-m", help="Regex pattern to include")
    filter_group.add_argument("--exclude", "-e", help="Regex pattern to exclude")
    filter_group.add_argument("--include-ext", help="Comma-separated extensions to include (e.g., php,asp)")
    filter_group.add_argument("--exclude-ext", help="Comma-separated extensions to exclude")
    filter_group.add_argument("--min-length", type=int, default=1, help="Minimum URL length")
    filter_group.add_argument("--max-length", type=int, default=2000, help="Maximum URL length")
    
    # Cache options
    cache_group = parser.add_argument_group('Cache Options')
    cache_group.add_argument("--cache", action="store_true", help="Enable caching")
    cache_group.add_argument("--cache-duration", type=int, default=86400, 
                            help="Cache duration in seconds (default: 86400 - 24 hours)")
    cache_group.add_argument("--no-cache", action="store_true", help="Disable caching")
    cache_group.add_argument("--clear-cache", action="store_true", help="Clear cache and exit")
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument("--output", "-o", help="Output file")
    output_group.add_argument("--format", "-f", choices=['txt', 'json', 'csv'], default='txt',
                             help="Output format (default: txt)")
    output_group.add_argument("--silent", "-q", action="store_true", 
                             help="Suppress all output except results")
    output_group.add_argument("--json", "-j", action="store_true", 
                             help="Alias for --format json")
    output_group.add_argument("--verbose", "-v", action="store_true", 
                             help="Verbose output")
    output_group.add_argument("--stats", action="store_true", 
                             help="Show statistics after collection")
    output_group.add_argument("--no-banner", action="store_true", 
                             help="Don't show banner")
    
    args = parser.parse_args()
    
    # Handle list providers
    if args.list_providers:
        print("\nAvailable providers (all free):")
        print("-" * 40)
        for key, name in UltimateGAU.PROVIDERS.items():
            print(f"  {key:15} - {name}")
        print()
        sys.exit(0)
    
    # Handle clear cache
    if args.clear_cache:
        cache_dir = Path.home() / ".gau_cache"
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            print(f"[+] Cache cleared: {cache_dir}")
        else:
            print("[!] No cache directory found")
        sys.exit(0)
    
    # Handle stdin input
    domains = []
    if args.stdin:
        domains = [line.strip() for line in sys.stdin if line.strip()]
    elif args.domain:
        domains = [args.domain]
    else:
        parser.error("Either provide a domain or use --stdin")
    
    # Parse providers
    if args.all:
        providers = list(UltimateGAU.PROVIDERS.keys())
    elif args.providers:
        providers = [p.strip() for p in args.providers.split(",")]
    else:
        providers = ['wayback', 'otx', 'commoncrawl', 'ukwa', 'arquivo']
    
    # Parse extensions
    include_ext = args.include_ext.split(',') if args.include_ext else None
    exclude_ext = args.exclude_ext.split(',') if args.exclude_ext else None
    
    # Determine output format
    output_format = 'json' if args.json else args.format
    
    # Process each domain
    all_results = []
    
    for domain in domains:
        # Create instance
        gau = UltimateGAU(
            domain=domain,
            subs=args.subs,
            providers=providers,
            threads=args.threads,
            timeout=args.timeout,
            match_pattern=args.match,
            exclude_pattern=args.exclude,
            include_extensions=include_ext,
            exclude_extensions=exclude_ext,
            min_length=args.min_length,
            max_length=args.max_length,
            use_cache=args.cache and not args.no_cache,
            cache_duration=args.cache_duration,
            rate_limit=args.rate_limit,
            silent=args.silent,
            json_output=(output_format == 'json'),
            verbose=args.verbose
        )
        
        # Show banner
        if not args.silent and not args.no_banner and domain == domains[0]:
            print(r"""
   _   _       _   _    __ _    _    _ 
  | | | |_ __ | |_| |_ / _| |_ / \  | |
  | | | | '_ \| __| __| |_| __/ _ \ | |
  | |_| | | | | |_| |_|  _| || ___ \| |___
   \___/|_| |_|\__|\__|_|  \__\_/ \_\_____|
                                           
   Ultimate GAU - Get All URLs (Free Edition)
            """, file=sys.stderr)
        
        # Run scan
        urls = gau.run()
        all_results.extend(gau.enriched_results)
        
        # Show statistics if requested
        if args.stats and not args.silent:
            stats = gau.get_statistics()
            print("\n[+] Statistics:", file=sys.stderr)
            print(f"    Total URLs: {stats['urls']['total']}", file=sys.stderr)
            print(f"    Unique domains: {stats['urls']['unique_domains']}", file=sys.stderr)
            
            if stats['urls']['file_extensions']:
                print("\n    Top extensions:", file=sys.stderr)
                for ext, count in list(stats['urls']['file_extensions'].items())[:5]:
                    print(f"      {ext}: {count}", file=sys.stderr)
    
    # Output results
    if all_results:
        if output_format == 'json':
            # Create combined JSON output for all domains
            combined_output = {
                'metadata': {
                    'tool': 'UltimateGAU',
                    'version': '3.0',
                    'timestamp': datetime.now().isoformat(),
                    'command': ' '.join(sys.argv)
                },
                'domains': domains,
                'total_urls': len(all_results),
                'urls': [asdict(url_data) for url_data in all_results]
            }
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(combined_output, f, indent=2)
            else:
                json.dump(combined_output, sys.stdout, indent=2)
                print()
        
        elif output_format == 'csv':
            if args.output:
                with open(args.output, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['url', 'scheme', 'domain', 'path', 'query', 
                                   'fragment', 'extension', 'parameters'])
                    for url_data in all_results:
                        writer.writerow([
                            url_data.url,
                            url_data.scheme,
                            url_data.domain,
                            url_data.path,
                            url_data.query,
                            url_data.fragment,
                            url_data.file_extension,
                            url_data.parameter_count
                        ])
            else:
                # Print to stdout
                writer = csv.writer(sys.stdout)
                writer.writerow(['url', 'scheme', 'domain', 'path', 'query', 
                               'fragment', 'extension', 'parameters'])
                for url_data in all_results:
                    writer.writerow([
                        url_data.url,
                        url_data.scheme,
                        url_data.domain,
                        url_data.path,
                        url_data.query,
                        url_data.fragment,
                        url_data.file_extension,
                        url_data.parameter_count
                    ])
        
        else:  # txt format
            output_handle = open(args.output, 'w') if args.output else sys.stdout
            try:
                for url_data in sorted(all_results, key=lambda x: x.url):
                    output_handle.write(url_data.url + '\n')
            finally:
                if args.output:
                    output_handle.close()
        
        if args.output and not args.silent:
            print(f"\n[+] Results saved to: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[-] Interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Error: {e}", file=sys.stderr)
        if 'verbose' in locals() and verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
