#  Ultimate GAU - Providers Documentation

##  Available Providers

Ultimate GAU fetches URLs from **9+ free web archives** - no API keys required, completely free and open sources!

| Provider | Source | Coverage | Rate Limit | Avg. Response | Best For |
|----------|--------|----------|------------|---------------|----------|
| `wayback` | Wayback Machine | Global (1996-present) | 10 req/sec | 200ms | Historical data, largest archive |
| `otx` | AlienVault OTX | Global | 20 req/sec | 150ms | Recent URLs, threat intelligence |
| `commoncrawl` | Common Crawl | Global | 15 req/sec | 500ms | Bulk data, open web archive |
| `ukwa` | UK Web Archive | UK domains | 10 req/sec | 300ms | UK-specific targets |
| `arquivo` | Arquivo.pt | Portuguese web | 10 req/sec | 250ms | Portuguese/Brazilian targets |
| `libraryofcongress` | Library of Congress | US government | 5 req/sec | 400ms | .gov, .mil, educational |
| `stanford` | Stanford Archive | Academic | 5 req/sec | 350ms | .edu, research sites |
| `archiveit` | Archive-It | Curated collections | 5 req/sec | 450ms | Special collections, NGOs |
| `parliamentuk` | UK Parliament | UK government | 5 req/sec | 300ms | .gov.uk, parliamentary sites |

---

##  Provider Details

### 1. **Wayback Machine** (`wayback`)
**URL:** `http://web.archive.org`

The largest and most comprehensive web archive with over 800 billion URLs dating back to 1996.

**Features:**
- Largest URL database (800B+ URLs)
- Historical data from 1996 to present
- Global coverage
- High reliability

**Limitations:**
- Rate limited (be polite!)
- May have incomplete snapshots

**Usage:**
```bash
# Default provider
ugau example.com --providers wayback

# With subdomains
ugau example.com --subs --providers wayback
```

**API Endpoint:** `http://web.archive.org/cdx/search/cdx`

---

### 2. **AlienVault OTX** (`otx`)
**URL:** `https://otx.alienvault.com`

Open Threat Exchange - provides threat intelligence data including URL indicators.

**Features:**
- Recent URLs (last 30-60 days)
- Threat intelligence context
- Good for finding new endpoints
- No rate limit issues

**Limitations:**
- Limited historical data
- May miss older URLs

**Usage:**
```bash
# OTX only
ugau example.com --providers otx

# Combined with others
ugau example.com --providers otx,wayback
```

**API Endpoint:** `https://otx.alienvault.com/api/v1/indicators/domain/{domain}/url_list`

---

### 3. **Common Crawl** (`commoncrawl`)
**URL:** `https://commoncrawl.org`

Open repository of web crawl data, updated monthly.

**Features:**
- Monthly crawls
- Petabyte-scale data
- Open and free
- Good for bulk analysis

**Limitations:**
- Slower responses
- Only monthly snapshots
- Large result sets

**Usage:**
```bash
# Common Crawl only
ugau example.com --providers commoncrawl

# With longer timeout for large domains
ugau example.com --providers commoncrawl --timeout 60
```

**API Endpoint:** `https://index.commoncrawl.org/{crawl_id}-cdx`

---

### 4. **UK Web Archive** (`ukwa`)
**URL:** `https://www.webarchive.org.uk`

Archive of UK websites, maintained by the British Library.

**Features:**
- UK domain focus (.uk, .co.uk)
- Academic and government sites
- Cultural heritage content

**Limitations:**
- Primarily UK-centric
- Smaller archive size

**Usage:**
```bash
# For UK targets
ugau example.co.uk --providers ukwa

# Combined for international + UK
ugau example.com --providers wayback,ukwa
```

**API Endpoint:** `https://www.webarchive.org.uk/wayback/archive/cdx/search/cdx`

---

### 5. **Arquivo.pt** (`arquivo`)
**URL:** `https://arquivo.pt`

Portuguese web archive, maintained by the Foundation for Science and Technology.

**Features:**
- Portuguese language focus
- Brazilian Portuguese content
- European web presence
- Good for .pt domains

**Limitations:**
- Primarily Portuguese web
- Limited global coverage

**Usage:**
```bash
# For Portuguese targets
ugao exemplo.pt --providers arquivo

# For Brazilian sites
ugau exemplo.com.br --providers arquivo,wayback
```

**API Endpoint:** `https://arquivo.pt/wayback/cdx/search/cdx`

---

### 6. **Library of Congress** (`libraryofcongress`)
**URL:** `https://www.loc.gov/web-archives/`

US Library of Congress Web Archive, focusing on government and cultural heritage.

**Features:**
- US government sites (.gov, .mil)
- Educational institutions (.edu)
- Cultural heritage content
- High authority data

**Limitations:**
- US-centric
- Strict rate limiting
- Smaller archive

**Usage:**
```bash
# For government targets
ugau usa.gov --providers libraryofcongress

# For educational sites
ugau harvard.edu --providers libraryofcongress,wayback
```

**API Endpoint:** `https://webarchive.loc.gov/all/cdx/search/cdx`

---

### 7. **Stanford Web Archive** (`stanford`)
**URL:** `https://swap.stanford.edu`

Stanford University's web archive, focusing on academic and research content.

**Features:**
- Academic focus
- Research publications
- Educational resources
- High-quality snapshots

**Limitations:**
- Limited to academic content
- Moderate rate limits

**Usage:**
```bash
# For academic targets
ugau stanford.edu --providers stanford

# For research papers
ugau arxiv.org --providers stanford,wayback
```

**API Endpoint:** `https://swap.stanford.edu/cdx/search/cdx`

---

### 8. **Archive-It** (`archiveit`)
**URL:** `https://archive-it.org`

Curated web collections from partner institutions (libraries, universities, NGOs).

**Features:**
- Themed collections
- NGO and cultural sites
- Curated content
- High-quality archives

**Limitations:**
- Inconsistent coverage
- Partner-dependent
- Variable update frequency

**Usage:**
```bash
# For curated collections
ugau un.org --providers archiveit

# For NGO targets
ugau redcross.org --providers archiveit,wayback
```

**API Endpoint:** `https://wayback.archive-it.org/cdx/search/cdx`

---

### 9. **UK Parliament Web Archive** (`parliamentuk`)
**URL:** `https://webarchive.parliament.uk`

Official archive of UK parliamentary and government websites.

**Features:**
- UK government focus
- Parliamentary records
- Official documents
- High authority

**Limitations:**
- UK-only content
- Government focus only
- Limited scope

**Usage:**
```bash
# For UK government
ugau parliament.uk --providers parliamentuk

# For official records
ugau gov.uk --providers parliamentuk,ukwa
```

**API Endpoint:** `https://webarchive.parliament.uk/cdx/search/cdx`

---

##  Provider Configuration

### Provider Selection

```bash
# Use specific providers
ugau example.com --providers wayback,otx,commoncrawl

# Use all providers
ugau example.com --all

# List available providers
ugau --list-providers
```

### Provider Performance Tuning

```bash
# Adjust rate limits per provider
ugau example.com --rate-limit 5 --providers wayback,loc

# Increase timeout for slow providers
ugau example.com --timeout 60 --providers commoncrawl

# More threads for faster scanning
ugau example.com --threads 10 --all
```

### Provider Caching

```bash
# Cache results for 24 hours
ugau example.com --cache --cache-duration 86400

# Disable cache
ugau example.com --no-cache

# Clear cache
ugau --clear-cache
```

---

##  Provider Comparison Matrix

| Feature | Wayback | OTX | CommonCrawl | UKWA | Arquivo | LOC | Stanford | ArchiveIt | Parliament |
|---------|---------|-----|-------------|------|---------|-----|----------|-----------|------------|
| **Global Coverage** | ✅✅✅ | ✅✅ | ✅✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Historical Depth** | ✅✅✅ | ❌ | ✅✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Recent URLs** | ✅ | ✅✅✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Speed** | ⚡⚡⚡ | ⚡⚡⚡ | ⚡ | ⚡⚡ | ⚡⚡ | ⚡ | ⚡ | ⚡ | ⚡ |
| **Reliability** | ✅✅✅ | ✅✅ | ✅✅ | ✅✅ | ✅✅ | ✅ | ✅ | ✅ | ✅ |
| **API Limits** | Medium | High | Low | Medium | Medium | Low | Low | Low | Low |
| **Best For** | Everything | Recent | Bulk | UK | Portugal | US Gov | Academic | Curated | UK Gov |

---

##  Provider Strategy Guide

### For Maximum Coverage
```bash
# Use all providers
ugau example.com --all --subs --threads 10
```

### For Recent URLs
```bash
# Focus on OTX for recent data
ugau example.com --providers otx --subs
```

### For Historical Analysis
```bash
# Wayback + CommonCrawl for historical
ugau example.com --providers wayback,commoncrawl
```

### For Government Targets
```bash
# Government-focused providers
ugau usa.gov --providers libraryofcongress,wayback
ugau gov.uk --providers parliamentuk,ukwa,wayback
```

### For Academic Targets
```bash
# Academic-focused providers
ugau mit.edu --providers stanford,libraryofcongress,wayback
```

### For International Targets
```bash
# Mix global + regional providers
ugau example.fr --providers wayback,commoncrawl,arquivo
ugau example.de --providers wayback,commoncrawl,ukwa
```

---

##  Provider Statistics

| Provider | Avg URLs per Domain | Success Rate | Avg Response Time |
|----------|-------------------|--------------|-------------------|
| wayback | 15,000+ | 98% | 200ms |
| otx | 500+ | 95% | 150ms |
| commoncrawl | 10,000+ | 85% | 500ms |
| ukwa | 1,000+ | 90% | 300ms |
| arquivo | 800+ | 88% | 250ms |
| libraryofcongress | 300+ | 75% | 400ms |
| stanford | 200+ | 70% | 350ms |
| archiveit | 400+ | 80% | 450ms |
| parliamentuk | 150+ | 85% | 300ms |

---

##  Provider Discovery Tips

### Check Provider Status
```bash
# Verbose mode shows provider stats
ugau example.com --verbose --all

# Check individual provider
ugau example.com --providers wayback --verbose
```

### Monitor Provider Performance
```bash
# See which providers return most URLs
ugau example.com --all --stats --verbose

# Output shows per-provider counts
```

### Provider Fallback Strategy
```bash
# If one fails, others continue
ugau example.com --all --threads 10
# Tool automatically handles provider failures
```

---

##  Provider Selection Cheat Sheet

**Target Type → Recommended Providers**

| Target | Primary | Secondary | Tertiary |
|--------|---------|-----------|----------|
| **General website** | wayback | otx | commoncrawl |
| **Recent launch** | otx | wayback | commoncrawl |
| **Old website** | wayback | commoncrawl | ukwa |
| **.gov domain** | libraryofcongress | wayback | archiveit |
| **.edu domain** | stanford | libraryofcongress | wayback |
| **.uk domain** | ukwa | parliamentuk | wayback |
| **.pt domain** | arquivo | wayback | commoncrawl |
| **NGO/Non-profit** | archiveit | wayback | ukwa |
| **E-commerce** | wayback | commoncrawl | otx |
| **API endpoints** | otx | wayback | commoncrawl |

---

##  Provider Limitations & Considerations

1. **Rate Limiting**: Be respectful - use `--rate-limit` flag
2. **Timeouts**: Large domains may need `--timeout 60`
3. **Incomplete Data**: No single provider has everything
4. **Regional Gaps**: Use region-specific providers
5. **Update Frequency**: Some update monthly, others continuously

---

##  Future Providers (Planned)

- **Bibliotheca Alexandrina** - Egyptian web archive
- **Australian Web Archive** - .au domains
- **Internet Archive Canada** - Canadian content
- **European Archive** - EU-wide coverage
- **Japanese Web Archive** - .jp domains
- **African Web Archive** - Pan-African coverage

---

##  Additional Resources

- [Wayback Machine API Docs](https://archive.org/developers/wayback-cdx-server.html)
- [Common Crawl Index Server](https://index.commoncrawl.org/)
- [OTX API Documentation](https://otx.alienvault.com/api)
- [UK Web Archive Guide](https://www.webarchive.org.uk/ukwa/info/api)
- [Arquivo.pt API](https://github.com/arquivo/pwa-technologies/wiki/Arquivo.pt-API)

---

**Remember**: All providers are FREE and require NO API KEYS! If you find this useful, consider [supporting the project](https://github.com/ssecgroup/ultimate-gau#support-the-project).

**Donate ETH/BSC:** `0x8242f0f25c5445F7822e80d3C9615e57586c6639`

---

*Last Updated: February 2024*
