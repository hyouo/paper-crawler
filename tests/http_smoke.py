"""Run separately so Eventlet patches sockets before the application is imported."""
import os
os.environ.setdefault('EVENTLET_NO_GREENDNS', 'yes')
import eventlet
eventlet.monkey_patch()

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config, database, paths, utils

WORKSPACE = tempfile.TemporaryDirectory()
ROOT = Path(WORKSPACE.name)
paths.PROJECT_ROOT = ROOT
paths.PAPER_ROOT = ROOT / 'paper'
paths.PAPER_ROOT.mkdir()
database.DB_PATH = str(ROOT / 'test.sqlite')
config.get_project_root = lambda: str(ROOT)
config.save_config({'categories': {'arxiv': []}, 'keywords': [],
                    'fetch_settings': {'method': 'category'}, 'custom': 'preserve'})
import app as web

class HttpTests(unittest.TestCase):
    def setUp(self):
        self.client = web.app.test_client()

    def test_file_serving_rejects_traversal_and_project_files(self):
        for url in ('/paper_files/../config.yaml', '/paper_files/config.yaml',
                    '/paper_files/paper/../../private.pdf'):
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_only_downloaded_pdf_is_served(self):
        (paths.PAPER_ROOT / 'allowed.pdf').write_bytes(b'%PDF-example')
        response = self.client.get('/paper_files/paper/allowed.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'%PDF-example')
        response.close()

    def test_open_routes_reject_untrusted_paths_without_launching_programs(self):
        with patch.object(web, '_open_path') as opener:
            for route in ('open_file', 'open_folder'):
                for path in ('../private.pdf', '/etc/passwd', 'config.yaml'):
                    self.assertEqual(self.client.post('/api/' + route, json={'filepath': path}).status_code, 400)
            opener.assert_not_called()

    def test_historical_absolute_download_path_is_supported(self):
        path = paths.PAPER_ROOT / 'legacy.pdf'
        path.write_bytes(b'%PDF-legacy')
        with patch.object(web, '_open_path', return_value=True) as opener:
            self.assertEqual(self.client.post('/api/open_file', json={'filepath': str(path)}).status_code, 200)
            opener.assert_called_once_with(str(path))

    def test_malformed_json_is_a_client_error(self):
        for route in ('config', 'papers/delete', 'open_file', 'open_folder'):
            for payload in ([], 'text', 3):
                self.assertEqual(self.client.post('/api/' + route, json=payload).status_code, 400)
            self.assertEqual(self.client.post('/api/' + route, data='{', content_type='application/json').status_code, 400)

    def test_config_patch_preserves_unedited_sections(self):
        response = self.client.post('/api/config', json={'keywords': ['updated']})
        self.assertEqual(response.status_code, 200)
        stored = config.load_config()
        self.assertEqual(stored['custom'], 'preserve')
        self.assertEqual(stored['fetch_settings']['method'], 'category')
        self.assertEqual(stored['keywords'], ['updated'])

    def test_delete_rejects_invalid_id_types(self):
        for value in ('1', [True], [-1], [1.2], []):
            self.assertEqual(self.client.post('/api/papers/delete', json={'paper_ids': value}).status_code, 400)

    def test_socket_invalid_requests_return_errors(self):
        self.assertEqual(web.handle_start_crawl([])['status'], 'error')
        self.assertEqual(web.handle_start_crawl({'categories': []})['status'], 'error')
        web.handle_download_papers([])

    def test_downloads_are_unique_portable_and_progress_uses_megabytes(self):
        events = []
        with patch.object(web.crawler, '_emit', side_effect=lambda event,data: events.append((event,data))):
            def download(url, path, referer, callback):
                callback(50, 1024**2, 2 * 1024**2)
                return True
            with patch.object(utils, 'download_pdf', side_effect=download):
                first = web.crawler._download_paper({'source':'arXiv', 'title':'same', 'pdf_url':'https://example.org/1.pdf'})
                second = web.crawler._download_paper({'source':'arXiv', 'title':'same', 'pdf_url':'https://example.org/2.pdf'})
        self.assertNotEqual(first, second)
        self.assertFalse(Path(first).is_absolute())
        self.assertIn('1.00/2.00 MB', events[0][1]['status'])

    def test_download_rejects_source_path_escape_before_creating_directory(self):
        with self.assertRaises(ValueError):
            web.crawler._download_paper({'source':'../../outside', 'title':'same', 'pdf_url':'https://example.org/1.pdf'})

if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        WORKSPACE.cleanup()
