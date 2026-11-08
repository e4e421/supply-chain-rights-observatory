# Accessibility QA protocol — WCAG 2.2 AA target (not certified)

**Scope:** English, Traditional Chinese and German pages; latest signals; historical archive explorer; individual record view. The current automated static checks are only regression safeguards, **not a WCAG conformance audit**.

## Manual test matrix (log device, date, browser, language and result)
1. **Keyboard only:** use Tab and Shift+Tab from page top. All links, search fields, archive month controls, CSV export and language switcher must be reachable, visible and activatable. No keyboard trap.
2. **Focus visibility:** every input/button/link must have a visible indicator not hidden by the sticky header; test WCAG 2.2 2.4.7 and 2.4.11.
3. **Contrast:** calculate normal text at ≥4.5:1, large text ≥3:1; also test non-text focus borders at ≥3:1 when applicable.
4. **Zoom:** use browser 200% and 400% with a 1280×720 desktop and a 320px responsive viewport. No loss of information or functionality; any horizontal scrolling only for content that genuinely requires it.
5. **Assistive technology:** NVDA + Firefox/Chrome on Windows and VoiceOver + Safari on macOS/iOS; headings, landmark names, select controls, status updates, archive results and errors should read clearly.
6. **Language:** confirm page `lang` follows selected English/zh-Hant/de. Original publication language is deliberately unspecified (`und`) unless independently known; evaluate reading impact.
7. **Dynamic interactions:** result count updates should be announced once without re-reading a full list; date filters and month changes must have understandable status.
8. **Touch targets:** verify important controls meet WCAG 2.2 2.5.8 (24×24 CSS px or spacing alternatives), preferably a 44px high design target.
9. **Reduced motion / forced colors:** respect `prefers-reduced-motion` and check high-contrast/forced-color operation.
10. **Error recovery:** unavailable archive/catalog and invalid record links should provide actionable, non-technical feedback.

## Evidence to retain
- Screenshots at 320px, desktop, 200% and 400% zoom, plus recorded browser/OS versions.
- axe-core and Lighthouse accessibility results, including manual inspection of false positives and missed issues.
- Keyboard/reader task completion log for each locale.
- Fixed issues linked to PR SHA and a re-test date.

**Release gate:** no unresolved critical barrier to browse, filter, view source, change language or export. Treat this as a quality target until all required automated and manual checks actually pass.
