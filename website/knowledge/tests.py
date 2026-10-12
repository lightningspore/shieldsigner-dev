from django.test import SimpleTestCase
from django.conf import settings
from .catalog import GUIDES

class KnowledgeTests(SimpleTestCase):
    def test_all_guides_and_metadata(self):
        for slug, *_ in GUIDES:
            response = self.client.get(f"/guides/{slug}/")
            self.assertEqual(response.status_code, 200, slug)
            self.assertContains(response, f'https://shieldsigner.dev/guides/{slug}/')
        self.assertEqual(self.client.get('/guides/not-a-guide/').status_code, 404)

    def test_search_and_progressive_enhancement(self):
        response = self.client.get('/guides/?q=SEC1210')
        self.assertContains(response, 'Cards &amp; the Linux reader')
        response = self.client.get('/guides/?q=SEC1210', HTTP_HX_REQUEST='true')
        self.assertNotContains(response, '<!doctype html>')
        self.assertContains(response, 'Cards &amp; the Linux reader')
        response = self.client.get('/guides/', HTTP_HX_REQUEST='true', HTTP_HX_BOOSTED='true')
        self.assertContains(response, '<!doctype html>')

    def test_download_boundary(self):
        self.assertEqual(self.client.get('/files/reference/pdfs/C5417011.pdf').status_code, 200)
        for path in ['../manage.py', '.env', 'tools/telegram/shieldsigner.txt', 'tools/telegram/account.session']:
            self.assertEqual(self.client.get('/files/'+path).status_code, 404)
        for path in settings.PUBLIC_DIR.rglob('*'):
            self.assertNotIn(path.suffix, {'.session', '.sqlite3', '.env'})

    def test_home_and_sitemap(self):
        self.assertContains(self.client.get('/'), 'Build it.')
        self.assertContains(self.client.get('/'), 'hardware bring-up')
        self.assertContains(self.client.get('/sitemap.xml'), 'https://shieldsigner.dev/guides/smartcards/')
