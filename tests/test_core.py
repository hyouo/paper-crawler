"""Filesystem/configuration regressions; no network or real paper database."""
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src import config, database, paths, utils


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(paths, 'PAPER_ROOT', tmp_path / 'paper')
    (tmp_path / 'paper' / 'arXiv').mkdir(parents=True)
    return tmp_path


@pytest.mark.parametrize('path', ['../outside.pdf', '/etc/passwd', 'config.yaml',
                                  'paper/../outside.pdf', 'paper-sibling/x.pdf',
                                  '', None, [], 'paper/a\x00.pdf'])
def test_reject_paths_outside_downloads(workspace, path):
    with pytest.raises(ValueError):
        paths.resolve_paper_path(path, must_exist=False)


def test_relative_and_historical_absolute_paths(workspace):
    paper = workspace / 'paper' / 'arXiv' / '论文.pdf'
    paper.write_bytes(b'%PDF-test')
    assert paths.resolve_paper_path('paper/arXiv/论文.pdf') == paper
    assert paths.resolve_paper_path(str(paper)) == paper
    with pytest.raises(FileNotFoundError):
        paths.resolve_paper_path('paper/missing.pdf')


def test_symlink_escape(workspace, tmp_path):
    outside = tmp_path / 'outside.pdf'
    outside.write_bytes(b'private')
    (workspace / 'paper' / 'link.pdf').symlink_to(outside)
    with pytest.raises(ValueError):
        paths.resolve_paper_path('paper/link.pdf')


@pytest.mark.parametrize('value', [None, [], 'text', {'categories': None},
                                   {'categories': {'arxiv': 'cs.AI'}},
                                   {'keywords': [3]}, {'fetch_settings': []}])
def test_invalid_config_preserves_existing_file(tmp_path, value):
    path = tmp_path / 'config.yaml'
    path.write_text('keywords: [original]\n', encoding='utf-8')
    assert config.save_config(value, str(path)) is False
    assert path.read_text() == 'keywords: [original]\n'
    assert not list(tmp_path.glob('.config-*'))


def test_config_replace_failure_preserves_previous_file(tmp_path):
    path = tmp_path / 'config.yaml'
    path.write_text('keywords: [original]\n')
    with patch.object(config.os, 'replace', side_effect=OSError('disk error')):
        assert config.save_config({'keywords': ['replacement']}, str(path)) is False
    assert config.load_config(str(path)) == {'keywords': ['original']}
    assert not list(tmp_path.glob('.config-*'))


def test_config_roundtrip_and_invalid_load(tmp_path):
    path = tmp_path / 'config.yaml'
    value = {'keywords': ['中文'], 'categories': {'arxiv': []}, 'custom': 42}
    assert config.save_config(value, str(path))
    assert config.load_config(str(path)) == value
    path.write_text('null\n')
    with pytest.raises(ValueError):
        config.load_config(str(path))


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / 'test.sqlite'
    path.touch()  # Regression: an existing zero-byte SQLite file still needs schema.
    monkeypatch.setattr(database, 'DB_PATH', str(path))
    database.init_db()
    return path


def paper_data(filepath='paper/test.pdf'):
    return dict(title='test', source='arXiv', paper_url='https://example.org/paper',
                pdf_url='https://example.org/paper.pdf', filepath=filepath)


def test_database_initialization_is_idempotent(db):
    key = database.add_paper(paper_data())
    assert key
    database.init_db()
    assert len(database.get_all_papers()) == 1
    assert database.is_paper_downloaded('https://example.org/paper.pdf')


def test_delete_checks_every_path_before_removing_records(db, workspace):
    key = database.add_paper(paper_data('../outside.pdf'))
    with pytest.raises(ValueError):
        database.delete_papers_by_ids([key], validate_filepath=lambda p:
                                     paths.resolve_paper_path(p, must_exist=False))
    assert len(database.get_all_papers()) == 1


def test_delete_sql_error_is_not_reported_as_success(db):
    with patch.object(database, 'get_db_connection', side_effect=sqlite3.OperationalError('locked')):
        with pytest.raises(sqlite3.OperationalError):
            database.delete_papers_by_ids([1])


def response(chunks, length=None):
    value = MagicMock()
    value.__enter__.return_value = value
    value.headers = {} if length is None else {'content-length': str(length)}
    value.iter_content.return_value = iter(chunks)
    return value


def test_existing_download_is_never_overwritten_or_deleted(tmp_path):
    path = tmp_path / 'paper.pdf'
    path.write_bytes(b'existing user data')
    with patch.object(utils.requests, 'get') as get:
        assert not utils.download_pdf('https://example.org/a.pdf', str(path))
    get.assert_not_called()
    assert path.read_bytes() == b'existing user data'


def test_complete_pdf_is_published_and_response_closed(tmp_path):
    path = tmp_path / 'paper.pdf'
    res = response([b'%PDF-', b'complete'], 13)
    progress = MagicMock()
    with patch.object(utils.requests, 'get', return_value=res):
        assert utils.download_pdf('https://example.org/a.pdf', str(path), progress_callback=progress)
    assert path.read_bytes() == b'%PDF-complete'
    res.__exit__.assert_called_once()
    progress.assert_called_with(100, 13, 13)
    assert not list(tmp_path.glob('.download-*'))


@pytest.mark.parametrize('chunks,length', [([], 0), ([b'<html>error'], 11),
                                         ([b'%PDF-partial'], 100)])
def test_invalid_or_truncated_response_leaves_no_download(tmp_path, chunks, length):
    path = tmp_path / 'paper.pdf'
    res = response(chunks, length)
    with patch.object(utils.requests, 'get', return_value=res):
        assert not utils.download_pdf('https://example.org/a.pdf', str(path), max_retries=1)
    assert not path.exists()
    assert not list(tmp_path.glob('.download-*'))


def test_interrupted_stream_cleans_only_temporary_file(tmp_path):
    def chunks():
        yield b'%PDF-start'
        raise requests.exceptions.ConnectionError('interrupted')
    path = tmp_path / 'paper.pdf'
    res = response(chunks())
    with patch.object(utils.requests, 'get', return_value=res):
        assert not utils.download_pdf('https://example.org/a.pdf', str(path), max_retries=1)
    assert not path.exists()
    assert not list(tmp_path.glob('.download-*'))
    res.__exit__.assert_called_once()


def test_racing_download_preserves_winner(tmp_path):
    path = tmp_path / 'paper.pdf'
    def chunks():
        yield b'%PDF-ours'
        path.write_bytes(b'%PDF-winner')
    with patch.object(utils.requests, 'get', return_value=response(chunks())):
        assert not utils.download_pdf('https://example.org/a.pdf', str(path), max_retries=1)
    assert path.read_bytes() == b'%PDF-winner'


def test_corrupt_database_fails_initialization(tmp_path, monkeypatch):
    path = tmp_path / 'corrupt.sqlite'
    path.write_bytes(b'not a sqlite database')
    monkeypatch.setattr(database, 'DB_PATH', str(path))
    with pytest.raises(sqlite3.DatabaseError):
        database.init_db()
    assert path.read_bytes() == b'not a sqlite database'
