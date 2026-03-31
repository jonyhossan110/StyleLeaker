from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment


class HTMLParser:
    """HTML parsing engine for StyleLeaker."""

    @staticmethod
    def _is_stylesheet_rel(value: Any) -> bool:
        if not value:
            return False
        if isinstance(value, str):
            return 'stylesheet' in value.lower()
        if isinstance(value, (list, tuple)):
            return any(isinstance(item, str) and 'stylesheet' in item.lower() for item in value)
        return False

    def parse(self, html: str, base_url: str) -> Dict[str, Any]:
        """Extract structure, assets, comments, and form data from HTML."""
        soup = BeautifulSoup(html, 'lxml')

        stylesheet_links: List[str] = []
        for link in soup.find_all('link', rel=self._is_stylesheet_rel):
            href = link.get('href')
            if href:
                stylesheet_links.append(urljoin(base_url, href.strip()))

        inline_styles: List[str] = []
        for style in soup.find_all('style'):
            content = style.string or style.get_text(separator='\n')
            if content.strip():
                inline_styles.append(content.strip())

        script_sources: List[str] = []
        for script in soup.find_all('script'):
            src = script.get('src')
            if src:
                script_sources.append(urljoin(base_url, src.strip()))

        comments: List[str] = []
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            normalized = str(comment).strip()
            if normalized:
                comments.append(normalized)

        meta_tags: List[Dict[str, str]] = []
        for meta in soup.find_all('meta'):
            attributes = {key: value for key, value in meta.attrs.items() if isinstance(value, str)}
            if attributes:
                meta_tags.append(attributes)

        class_names: set[str] = set()
        id_names: set[str] = set()
        for tag in soup.find_all(True):
            classes = tag.get('class')
            if classes:
                for class_name in classes:
                    if isinstance(class_name, str) and class_name.strip():
                        class_names.add(class_name.strip())
            element_id = tag.get('id')
            if element_id and isinstance(element_id, str):
                id_names.add(element_id.strip())

        forms: List[Dict[str, Any]] = []
        for form in soup.find_all('form'):
            action = form.get('action', '').strip()
            method = form.get('method', 'get').strip().lower()
            fields: List[Dict[str, str]] = []
            for input_tag in form.find_all(['input', 'textarea', 'select']):
                name = input_tag.get('name', '').strip()
                value = input_tag.get('value', '').strip() if input_tag.get('value') else ''
                field_type = input_tag.get('type', 'text').strip().lower()
                fields.append({
                    'name': name,
                    'type': field_type,
                    'value': value,
                })
            forms.append({
                'action': urljoin(base_url, action) if action else base_url,
                'method': method,
                'fields': fields,
            })

        return {
            'stylesheet_links': sorted(set(stylesheet_links)),
            'inline_styles': inline_styles,
            'script_sources': sorted(set(script_sources)),
            'comments': comments,
            'meta_tags': meta_tags,
            'class_names': sorted(class_names),
            'id_names': sorted(id_names),
            'forms': forms,
        }
