from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from core.analyzer import Analyzer
from core.css_extractor import CSSExtractor
from core.fetcher import Fetcher
from core.html_parser import HTMLParser
from core.js_crossref import JSCrossRef
from core.recon import Recon
from core.reporter import Reporter
from core.severity import SeverityScorer
from utils.file_handler import build_output_paths, save_text_file
from utils.logger import Logger

VERSION = '1.0.0'
BANNER = r'''
 ____  _         _      _               _             
/ ___|| |_ _   _| | ___| |    ___  __ _| | _____ _ __ 
\___ \| __| | | | |/ _ \ |   / _ \/ _` | |/ / _ \ '__|
 ___) | |_| |_| | |  __/ |__|  __/ (_| |   <  __/ |   
|____/ \__|\__, |_|\___|_____\___\__,_|_|\_\___|_|   
           |___/                                        
  v1.0.0 | By HexaCyberLab | Web CyberSecurity Tool |

+-------------------------------------------------------+
|  Created By: Md. Jony Hassain (HexaCyberLab)           |
|  LinkedIn: https://www.linkedin.com/in/jonyhossan110/  |  
|   https://github.com/jonyhossan110/StyleLeaker         |
+--------------------------------------------------------+
'''


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='StyleLeaker - Extract HTML and CSS assets for web security research')
    parser.add_argument('-u', '--url', required=True, help='Target URL')
    parser.add_argument('-o', '--output', default='./output', help='Output directory')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='Request timeout in seconds')
    parser.add_argument('-p', '--proxy', help='Proxy URL (e.g., http://127.0.0.1:8080)')
    parser.add_argument('--no-download', action='store_true', help='Only analyze, do not save CSS files')
    parser.add_argument('--no-recon', action='store_true', help='Skip robots.txt and header analysis')
    parser.add_argument('--severity-only', action='store_true', help='Only show HIGH and CRITICAL findings')
    parser.add_argument('--output-format', choices=['pdf', 'txt', 'both'], default='both', help='Choose output format')
    parser.add_argument('--depth', type=int, default=2, help='CSS @import recursion depth')
    parser.add_argument('--user-agent', help='Custom user agent string')
    parser.add_argument('--auth-cookie', help='Cookie string for authenticated page scanning')
    parser.add_argument('--cookies', help='Cookies string for authenticated scans')
    parser.add_argument('--headers', help='Extra headers as JSON string')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='store_true', help='Show tool version')
    parser.add_argument('--no-verify', action='store_true', help='Disable SSL verification')
    return parser.parse_args()


def normalize_target_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if ':' in domain:
        domain = domain.split(':')[0]
    return domain.replace('/', '_')


def parse_headers(headers: Optional[str], logger: Logger) -> Optional[Dict[str, str]]:
    if not headers:
        return None
    try:
        parsed = json.loads(headers)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
        logger.error('Headers must be a JSON object')
    except json.JSONDecodeError as exc:
        logger.error(f'Invalid headers JSON: {exc}')
    return None


def positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return ivalue


def main() -> int:
    args = parse_arguments()
    logger = Logger(verbose=args.verbose)

    if args.version:
        print(VERSION)
        return 0

    print(BANNER)
    logger.info('Starting StyleLeaker scan')

    target_url = args.url.strip()
    if not target_url:
        logger.error('No URL supplied. Use -u or --url to specify a target.')
        return 1

    if not urlparse(target_url).scheme:
        target_url = f'http://{target_url}'

    try:
        parsed = urlparse(target_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError('Invalid URL format')
    except ValueError:
        logger.error(f'Invalid URL: {target_url}')
        return 1

    output_base = Path(args.output).resolve()
    domain_name = normalize_target_domain(target_url)
    output_paths = build_output_paths(output_base, domain_name)

    fetcher = Fetcher(logger=logger)
    headers = parse_headers(args.headers, logger)
    cookie_string = args.auth_cookie or args.cookies
    response = fetcher.fetch(
        target_url,
        timeout=args.timeout,
        headers=headers,
        proxy=args.proxy,
        cookies=cookie_string,
        verify=not args.no_verify,
        user_agent=args.user_agent,
    )

    if not response:
        logger.error('Failed to fetch target URL. Aborting scan.')
        return 1

    logger.success(f'Fetched {target_url} with status {response.status_code}')
    html_text = response.text
    save_text_file(output_paths['html'] / 'page.html', html_text)
    logger.info(f'Saved HTML dump to {output_paths["html"] / "page.html"}')

    recon_data: Dict[str, Any] = {}
    if args.no_recon:
        logger.info('Skipping reconnaissance phase as requested')
    else:
        recon_module = Recon(fetcher, logger)
        recon_data = recon_module.run(target_url, response)
        logger.info('Reconnaissance complete')

    parser = HTMLParser()
    html_data = parser.parse(html_text, target_url)
    logger.info(f'Parsed HTML structure: {len(html_data.get("stylesheet_links", []))} stylesheet links found')

    for index, style in enumerate(html_data.get('inline_styles', []), start=1):
        inline_path = output_paths['html'] / f'inline-style-{index}.css'
        save_text_file(inline_path, style)
    if html_data.get('inline_styles'):
        logger.info(f'Saved {len(html_data["inline_styles"])} inline style block(s)')

    css_extractor = CSSExtractor(
        fetcher=fetcher,
        logger=logger,
        no_download=args.no_download,
        max_depth=args.depth,
    )

    css_results = css_extractor.extract(
        html_data.get('stylesheet_links', []),
        target_url,
        output_paths['css'],
    )

    logger.success(f'CSS analysis complete: {len(css_results)} file(s) processed')

    js_crossref = JSCrossRef()
    js_data = js_crossref.analyze(html_data, css_results)
    logger.info(f'JS cross-reference discovered {len(js_data.get("libraries", []))} JavaScript libraries')

    analyzer = Analyzer()
    analysis = analyzer.analyze(html_data, css_results)

    severity_scorer = SeverityScorer()
    severity_data = severity_scorer.score(analysis, recon_data, js_data)

    if args.severity_only:
        logger.info('Severity-only mode active; displaying only HIGH and CRITICAL findings:')
        for finding in severity_data.get('findings_list', []):
            if finding.get('severity') in {'CRITICAL', 'HIGH'}:
                logger.found(f"{finding.get('severity')}: {finding.get('finding')} ({finding.get('count')})")

    reporter = Reporter(logger)
    reporter.generate_report(
        target_url,
        output_paths['root'],
        analysis,
        recon_data=recon_data,
        js_data=js_data,
        severity_data=severity_data,
        output_format=args.output_format,
        severity_only=args.severity_only,
    )

    logger.success('StyleLeaker scan completed successfully')
    return 0


if __name__ == '__main__':
    sys.exit(main())
