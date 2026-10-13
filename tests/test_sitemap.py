import unittest
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree


@unittest.skipUnless(Path('site/sitemap.xml').exists(), 'Run mkdocs build first')
class SitemapTests(unittest.TestCase):
    def test_only_canonical_pages_with_matching_language_alternates_are_listed(self):
        namespace = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
        entries = ElementTree.parse('site/sitemap.xml').getroot().findall('s:url', namespace)
        self.assertTrue(entries)
        seen = set()
        for entry in entries:
            url = entry.findtext('s:loc', namespaces=namespace)
            with self.subTest(url=url):
                self.assertTrue(url.startswith('https://wiki.bxirobotics.com/'))
                self.assertNotIn(url, seen)
                seen.add(url)
                path = urlparse(url).path
                self.assertFalse(path.startswith('/en/'))
                base = path.removeprefix('/zh') if path.startswith('/zh/') else path
                alternates = {node.attrib['hreflang']: node.attrib['href'] for node in entry.findall('x:link', namespace)}
                self.assertEqual(alternates.get('en'), 'https://wiki.bxirobotics.com' + base)
                self.assertEqual(alternates.get('zh'), 'https://wiki.bxirobotics.com/zh' + base)
                html = Path('site', path.strip('/'), 'index.html').read_text(encoding='utf-8')
                self.assertNotIn('noindex, follow', html)
                if not path.startswith('/zh/'):
                    self.assertTrue(Path('site/en', path.strip('/'), 'index.html').is_file())


if __name__ == '__main__':
    unittest.main()
