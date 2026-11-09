"""Regression contracts for adaptive, non-scrolling result pages."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'docs/workbench/workbench.js').read_text(encoding='utf-8')
CSS = (ROOT / 'docs/workbench/pagination.css').read_text(encoding='utf-8')

class PaginationTests(unittest.TestCase):
    def test_only_current_page_rows_are_rendered(self):
        self.assertIn('filtered.slice(start,end)', JS)
        self.assertIn('MAX_PAGE_SIZE=40', JS)
        self.assertNotIn('visible+=PAGE', JS)
        self.assertIn('window.addEventListener(\'resize\',schedulePageLayout', JS)
        self.assertIn('ResizeObserver', JS)

    def test_paging_controls_are_accessible_and_localised(self):
        for label in ('Previous page', 'Next page', 'Results pagination'):
            self.assertIn(label, JS)
        self.assertIn("previous.setAttribute('aria-controls','wb-tbody')", JS)
        self.assertIn("status.setAttribute('aria-live','polite')", JS)
        self.assertIn("$('wb-prev').disabled=loading||!pages||pageIndex===0", JS)
        self.assertIn("$('wb-next').disabled=loading||!pages||pageIndex>=pages-1", JS)

    def test_no_nested_vertical_scroll_or_lost_full_text(self):
        self.assertIn('overflow-y:hidden', CSS)
        self.assertIn('max-height:none', CSS)
        self.assertIn('cell.title=value', JS)
        self.assertIn("out.append(text('h3',item.title))", JS)
        self.assertNotIn('innerHTML', JS)

    def test_exports_and_record_links_are_not_page_limited(self):
        self.assertIn('filtered.map(r=>columns.map', JS)
        self.assertIn("url.searchParams.set('offset'", JS)
        self.assertIn('locateSelection=Boolean(chosen)', JS)
        self.assertIn('pageAnchor=at;drawTable()', JS)

if __name__ == '__main__':
    unittest.main()
