# StyleLeaker

StyleLeaker is a professional Python CLI tool for web penetration testing and security research. It extracts HTML structure, CSS assets, inline styles, and security hints from a target website to help bug bounty hunters, pentesters, and security analysts identify hidden assets and framework info.

## Installation

1. Clone or download the repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python styleleaker.py -u https://target.com -o ./output
```

## Development and Testing

Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run local checks:

```bash
python -m compileall .
pytest -q
```

### Example commands

- Basic scan:
  ```bash
  python styleleaker.py -u https://example.com
  ```

- Custom output folder:
  ```bash
  python styleleaker.py -u https://example.com -o ./output/example
  ```

- Use Burp proxy:
  ```bash
  python styleleaker.py -u https://example.com -p http://127.0.0.1:8080
  ```

- Skip CSS downloads:
  ```bash
  python styleleaker.py -u https://example.com --no-download
  ```

- Add custom headers and cookies:
  ```bash
  python styleleaker.py -u https://example.com --headers '{"X-Test":"1"}' --cookies 'SESSIONID=abc123'
  ```

## CLI Flags

- `-u, --url` : Target URL (required)
- `-o, --output` : Output directory (default: `./output`)
- `-t, --timeout` : Request timeout in seconds (default: `10`)
- `-p, --proxy` : Proxy URL for Burp Suite or other proxy
- `--no-download` : Only analyze, do not save CSS files
- `--no-recon` : Skip robots.txt and header analysis
- `--severity-only` : Only show HIGH and CRITICAL findings
- `--output-format` : Choose output format: `pdf`, `txt`, or `both` (default: `both`)
- `--depth` : CSS `@import` recursion depth (default: `2`)
- `--user-agent` : Custom user agent string
- `--auth-cookie` : Cookie string for authenticated page scanning
- `--cookies` : Cookies string for authenticated scans
- `--headers` : Extra headers as JSON string
- `-v, --verbose` : Verbose output
- `--version` : Show tool version
- `--no-verify` : Disable SSL verification

## Output

The tool creates an output folder structure for each scan:

```text
output/
  target-domain.com/
    css/
    html/
    report.txt
```

- `css/` contains downloaded CSS assets
- `html/` contains the root HTML dump and inline style blocks
- `report.txt` contains the scan summary and findings
- `report.pdf` contains the full formatted professional report

## Legal Disclaimer

Use StyleLeaker only for authorized security research, ethical hacking, and bug bounty programs. Do not scan systems without permission. Unauthorized scanning may violate the law.

## Author

Md. Jony Hassain | HexaCyberLab

- GitHub: https://github.com/jonyhossan110
- LinkedIn: https://www.linkedin.com/in/jonyhossan110
- Upwork: https://www.upwork.com/freelancers/~jonyhossan110
