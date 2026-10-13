import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from hooks import redirect_empty_sections as redirects


class RedirectSeoTests(unittest.TestCase):
    def test_locale_roots_have_metadata_and_keep_their_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(
                site_dir=directory,
                site_url='https://wiki.bxirobotics.com',
                extra={'alternate': [{'link': '/zh/', 'lang': 'zh'}, {'link': '/', 'lang': 'en'}]},
            )
            redirects.on_post_build(config)
            for prefix, language in [('zh/', 'zh'), ('', 'en')]:
                html = Path(directory, prefix, 'index.html').read_text(encoding='utf-8')
                self.assertIn(f'<html lang="{language}">', html)
                self.assertIn('<title>', html)
                self.assertIn('<meta name="description" content="', html)
                self.assertEqual(html.count('<h1>'), 1)
                self.assertIn(f'href="https://wiki.bxirobotics.com/{prefix}elf3/overview/"', html)
                self.assertIn('content="0; url=elf3/overview/"', html)

    def test_empty_section_redirect_is_not_indexed_as_a_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, 'index.zh.md')
            source.write_text('---\ntitle: ELF3\n---\n', encoding='utf-8')
            page = SimpleNamespace(file=SimpleNamespace(src_path='elf3/index.zh.md', abs_src_path=source), meta={}, canonical_url='https://wiki.bxirobotics.com/zh/elf3/')
            redirects._section_redirects['elf3'] = 'zh/elf3/overview/'
            config = SimpleNamespace(site_url='https://wiki.bxirobotics.com/')
            html = redirects.on_page_content('', page, config, None)
            self.assertIn('/zh/elf3/overview/', html)
            self.assertEqual(page.meta['robots'], 'noindex, follow')
            self.assertEqual(page.canonical_url, 'https://wiki.bxirobotics.com/zh/elf3/')

    def test_old_english_paths_have_redirect_files_without_recursive_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            for route in ['elf3/overview', 'zh/elf3/overview']:
                path = Path(directory, route, 'index.html')
                path.parent.mkdir(parents=True)
                path.write_text('<h1>ELF3</h1>', encoding='utf-8')
            config = SimpleNamespace(site_dir=directory, site_url='https://wiki.bxirobotics.com', extra={'alternate': []})
            redirects.on_post_build(config)
            redirects.on_post_build(config)
            alias = Path(directory, 'en/elf3/overview/index.html').read_text(encoding='utf-8')
            self.assertIn('https://wiki.bxirobotics.com/elf3/overview/', alias)
            self.assertIn('location.search', alias)
            self.assertIn('location.hash', alias)
            self.assertFalse(Path(directory, 'en/en').exists())
            self.assertFalse(Path(directory, 'en/zh').exists())

    def test_real_content_is_not_redirected(self):
        page = SimpleNamespace(file=SimpleNamespace(src_path='elf3/overview.en.md'))
        self.assertEqual(redirects.on_page_content('<h1>ELF3</h1>', page, None, None), '<h1>ELF3</h1>')


if __name__ == '__main__':
    unittest.main()
