# Ultimate GAU - Complete Documentation

## Repository: [github.com/ssecgroup/ultimate-gau](https://github.com/ssecgroup/ultimate-gau)

---

# Ultimate GAU (Get All URLs)

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)](CONTRIBUTING.md)
[![Twitter](https://img.shields.io/twitter/url?style=social&url=(https://github.com/ssecgroup/ultimate-gau))](https://twitter.com/intent/tweet?text=Ultimate%20GAU%20-%20The%20most%20advanced%20free%20URL%20gathering%20tool&url=https://github.com/ssecgroup/ultimate-gau)

**Ultimate GAU** is a powerful, free, and open-source tool for fetching archived URLs from multiple web archives. It's designed for bug bounty hunters, security researchers, and penetration testers who need comprehensive URL discovery without paying for API keys.

![Ultimate GAU Demo](docs/demo.gif)

##  Features

- **9+ Free Providers** - No API keys required, all completely free
- **Silent Mode** - Perfect for piping to other tools (`httpx`, `nuclei`, etc.)
- **JSON Output** - Rich metadata for each URL
- **Smart Caching** - Avoid redundant requests, save bandwidth
- **Advanced Filtering** - Regex patterns, extensions, length filters
- **Multiple Output Formats** - TXT, JSON, CSV
- **Rate Limiting** - Be polite to archive servers
- **Concurrent Fetching** - Blazing fast multi-threaded scanning
- **URL Enrichment** - Extract parameters, paths, file types
- **Statistics Generation** - Understand your data better
- **Stdin Support** - Process multiple domains easily
- **Cross-Platform** - Works on Linux, macOS, Windows

##  Quick Installation

### Using pip (Recommended)
```bash
pip install ultimate-gau
```

### From Source
```bash
git clone https://github.com/ssecgroup/ultimate-gau.git
cd ultimate-gau
pip install -r requirements.txt
chmod +x ultimate_gau.py
sudo ln -s $(pwd)/ultimate_gau.py /usr/local/bin/ugau
```

### Using Docker
```bash
docker pull ssecgroup/ultimate-gau
docker run --rm ssecgroup/ultimate-gau example.com --subs
```

##  Requirements

```txt
# requirements.txt
requests>=2.25.0
tqdm>=4.62.0      # Optional - for progress bars
validators>=0.18.0 # Optional - for URL validation
```

##  Basic Usage

### Simple domain scan
```bash
python ultimate_gau.py example.com
```

### Include subdomains
```bash
python ultimate_gau.py example.com --subs
```

### Save to file
```bash
python ultimate_gau.py example.com --subs --output urls.txt
```

### Use specific providers
```bash
python ultimate_gau.py example.com --providers wayback,otx,commoncrawl
```

### Silent mode (URLs only)
```bash
python ultimate_gau.py example.com --silent
```

### JSON output with all providers
```bash
python ultimate_gau.py example.com --subs --all --json > results.json
```

##  Advanced Usage

### Complex filtering
```bash
# Match API endpoints, exclude images
python ultimate_gau.py example.com --subs \
  --match "api|v1|v2|graphql" \
  --exclude "\.jpg|\.png|\.css|\.js" \
  --verbose
```

### Extension filtering
```bash
# Only PHP and ASP files
python ultimate_gau.py example.com --subs \
  --include-ext php,asp,aspx,jsp \
  --output endpoints.txt
```

### Process multiple domains
```bash
cat domains.txt | python ultimate_gau.py --stdin --subs --all --silent > all_urls.txt
```

### With caching (24 hours)
```bash
python ultimate_gau.py example.com --subs --cache --cache-duration 86400
```

### Export statistics
```bash
python ultimate_gau.py example.com --subs --all --stats --verbose
```

### CSV export for analysis
```bash
python ultimate_gau.py example.com --subs --format csv --output analysis.csv
```

##  Output Formats

### Text Format (Default)
```
http://example.com/page1
https://example.com/api/v1/users
https://sub.example.com/admin.php?id=1
```

### JSON Format (Rich Metadata)
```json
{
  "metadata": {
    "tool": "UltimateGAU",
    "version": "3.0",
    "timestamp": "2024-01-15T10:30:00",
    "command": "ugau example.com --json"
  },
  "statistics": {
    "total_urls": 1523,
    "unique_domains": 8,
    "file_extensions": {".php": 450, ".html": 320}
  },
  "urls": [
    {
      "url": "https://example.com/api/v1/users",
      "scheme": "https",
      "domain": "example.com",
      "path": "/api/v1/users",
      "query": "",
      "fragment": "",
      "file_extension": "",
      "parameter_count": 0,
      "source": "gau"
    }
  ]
}
```

### CSV Format
```csv
url,scheme,domain,path,query,extension,parameters
https://example.com/api,https,example.com,/api,,,0
```

##  Real-World Examples

### Bug Bounty Pipeline
```bash
# Complete reconnaissance pipeline
echo target.com | ugau --stdin --subs --all --silent | \
  httpx -silent | \
  nuclei -t ~/nuclei-templates/ -o vulnerabilities.txt
```

### Parameter Discovery
```bash
# Find all URLs with parameters
ugau example.com --subs --silent | grep "?.*=" > parameters.txt

# Extract unique parameter names
ugau example.com --subs --silent | grep -oP '(?<=\?)[^=&]+' | sort -u
```

### API Endpoint Discovery
```bash
# Find API endpoints
ugau example.com --subs --match "api|graphql|v1|v2|rest" --silent
```

### Technology Stack Detection
```bash
# Find files that reveal technology
ugau example.com --subs --include-ext php,asp,jsp,py,rb,go --silent
```

##  Providers List

| Provider | Source | Description | Rate Limit |
|----------|--------|-------------|------------|
| `wayback` | Wayback Machine | Largest web archive | 10 req/sec |
| `otx` | AlienVault OTX | Threat intelligence | 20 req/sec |
| `commoncrawl` | Common Crawl | Open web archive | 15 req/sec |
| `ukwa` | UK Web Archive | UK sites | 10 req/sec |
| `arquivo` | Arquivo.pt | Portuguese archive | 10 req/sec |
| `libraryofcongress` | Library of Congress | US government | 5 req/sec |
| `stanford` | Stanford Archive | Academic archive | 5 req/sec |
| `archiveit` | Archive-It | Curated collections | 5 req/sec |
| `parliamentuk` | UK Parliament | Government sites | 5 req/sec |

##  Configuration

### Cache Management
```bash
# Clear cache
ugau --clear-cache

# Use cache for 48 hours
ugau example.com --cache --cache-duration 172800
```

### Rate Limiting
```bash
# Slow and polite (2 requests/sec)
ugau example.com --rate-limit 2 --threads 1

# Fast scanning (20 requests/sec)
ugau example.com --rate-limit 20 --threads 10
```

##  Contributing

  contributions welcome! Here's how you can help:

### Ways to Contribute
1. **Add new providers** - Find more free web archives
2. **Improve performance** - Optimize fetching algorithms
3. **Fix bugs** - Report or fix issues
4. **Documentation** - Improve guides and examples
5. **Feature requests** - Suggest new capabilities

### Development Setup
```bash
# Fork the repository
git clone https://github.com/YOUR_USERNAME/ultimate-gau.git
cd ultimate-gau

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

### Pull Request Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 💖 Support the Project

If you find this tool useful, consider supporting its development:

**Cryptocurrency Donations:**
- **ETH/BSC:** `0x8242f0f25c5445F7822e80d3C9615e57586c6639`
- **Bitcoin:** `bc1q...` (coming soon)

**Other ways to support:**
- ⭐ Star the repository
-  Share on Twitter
-  Write blog posts
-  Report bugs
-  Suggest features

##  Roadmap

### Version 3.1 (Q2 2024)
- [ ] Add 5 more free providers
- [ ] Web interface for easy scanning
- [ ] Export to Burp Suite format
- [ ] Real-time URL validation

### Version 3.2 (Q3 2024)
- [ ] Machine learning for parameter discovery
- [ ] Integration with popular tools
- [ ] Distributed scanning support
- [ ] Mobile app (iOS/Android)

### Version 4.0 (Q4 2024)
- [ ] Cloud scanning service
- [ ] Real-time collaboration
- [ ] Advanced analytics dashboard
- [ ] API for developers

##  Documentation

- [Full Documentation](docs/README.md)
- [Provider Details](docs/providers.md)
- [Filtering Guide](docs/filtering.md)
- [API Reference](docs/api.md)
- [FAQ](docs/faq.md)

##  Known Issues

- Some providers may have rate limits
- Very large domains might timeout
- Windows users need Python 3.7+

##  License

MIT License - see [LICENSE](LICENSE) file for details.

##  Contributors

- **@ssecgroup** - Project Lead
- **Community** - [View all contributors](https://github.com/ssecgroup/ultimate-gau/graphs/contributors)

##  Acknowledgments

- Inspired by [lc/gau](https://github.com/lc/gau)
- Thanks to all free web archives
- Bug bounty community for feedback

##  Contact

- **GitHub Issues:** [Report bugs](https://github.com/ssecgroup/ultimate-gau/issues)
- **Twitter:** [@ssecgroup](https://twitter.com/https://x.com/shiyanthans)
- **Email:**  ssecgroup08@gmail.com
- **Discord:** [Join our server](https://discord.gg/pr0xc3)

---

**Made with ❤️ by [@ssecgroup](https://github.com/ssecgroup)**

[![GitHub stars](https://img.shields.io/github/stars/ssecgroup/ultimate-gau?style=social)](https://github.com/ssecgroup/ultimate-gau/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ssecgroup/ultimate-gau?style=social)](https://github.com/ssecgroup/ultimate-gau/network/members)
[![GitHub watchers](https://img.shields.io/github/watchers/ssecgroup/ultimate-gau?style=social)](https://github.com/ssecgroup/ultimate-gau/watchers)

---

##  Quick Start Commands

```bash
# Installation
pip install ultimate-gau

# Basic scan
ugau example.com

# Full scan with all features
ugau example.com --subs --all --json --stats --verbose --output full_scan.json

# Pipeline with other tools
ugau example.com --subs --silent | httpx -silent | nuclei -t cves/ -o findings.txt

# Batch processing
cat domains.txt | ugau --stdin --subs --all --silent --output master_urls.txt

# Support the project
# Donate ETH: 0x8242f0f25c5445F7822e80d3C9615e57586c6639
```

---

**Remember to ⭐ star the repository if you find it useful!**
