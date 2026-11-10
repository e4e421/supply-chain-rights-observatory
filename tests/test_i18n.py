"""Language contract regression tests: English remains the canonical source of truth."""
import json
import re
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'docs/index.html').read_text(encoding='utf-8')
I18N=(ROOT/'docs/i18n.js').read_text(encoding='utf-8')
JS=(ROOT/'docs/app.js').read_text(encoding='utf-8')
QUERY=json.loads((ROOT/'sources/queries.json').read_text(encoding='utf-8'))
REFS=json.loads((ROOT/'docs/data/references.json').read_text(encoding='utf-8'))
COLLECTOR=(ROOT/'scripts/update_data.py').read_text(encoding='utf-8')
CJK=re.compile(r'[\u3400-\u9fff]')

class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values=[]
        self.titles=[]
    def handle_data(self,value):
        if value.strip():
            self.values.append(value.strip())
    def handle_starttag(self,tag,attrs):
        if tag == 'html':
            self.titles.append(dict(attrs).get('lang'))

class LocalisationContractTests(unittest.TestCase):
    def test_canonical_page_has_english_source_text(self):
        parser=PageText()
        parser.feed(HTML)
        self.assertEqual(parser.titles,['en'])
        self.assertIn('English',parser.values)
        self.assertIn('Deutsch',parser.values)
        self.assertIn('繁體中文',parser.values)
        self.assertEqual([x for x in parser.values if CJK.search(x)],['繁體中文'])
        self.assertIn('src="./i18n.js"',HTML)
        self.assertIn('id="language-select"',HTML)
        self.assertLess(HTML.index('src="./i18n.js"'), HTML.index('src="./app.js"'))

    def test_english_dictionary_is_both_complete_and_canonical(self):
        match=re.search(r'const dictionaries = (\{[^\n]+\});',I18N)
        self.assertIsNotNone(match,'Missing translation dictionary')
        translations=json.loads(match.group(1))
        self.assertGreater(len(translations),180)
        for key,translations_by_locale in translations.items():
            self.assertFalse(CJK.search(key),f'Non-English canonical string: {key}')
            self.assertTrue(translations_by_locale.get('zh'),key)
            self.assertTrue(translations_by_locale.get('de'),key)
        self.assertIn('Supply networks',translations)
        self.assertIn('Forced labour',translations)
        self.assertIn("Workers' rights & remedy",translations)
        self.assertIn('No verified successful collection yet. Check GitHub Actions.',translations)
        self.assertIn('localStorage.setItem',I18N)
        self.assertIn("url.searchParams.set('lang',code)",I18N)

    def test_all_public_data_generation_is_in_english(self):
        for query in QUERY['news_queries']+QUERY['academic_queries']:
            self.assertFalse(CJK.search(query['name']))
        for ref in REFS:
            self.assertFalse(CJK.search(ref['use']))
            self.assertFalse(CJK.search(ref['mode']))
        self.assertNotIn('自動發現的新聞聚合線索',COLLECTOR)
        self.assertNotIn('Crossref 出版書目資料',COLLECTOR)
        self.assertIn('News lead collected from a public feed',COLLECTOR)
        self.assertIn('Crossref bibliographic record',COLLECTOR)

    def test_dynamic_ui_and_public_access_boundaries(self):
        self.assertIn('textContent',JS)
        self.assertNotIn('.innerHTML',JS)
        self.assertIn('i18n.onChange(()=>render())',JS)
        self.assertIn("const columns=['title'",JS)
        self.assertNotIn('api_key',JS.lower())
        self.assertIn('textContent',I18N) if 'textContent' in I18N else self.assertIn('node.nodeValue',I18N)

if __name__=='__main__':
    unittest.main()
