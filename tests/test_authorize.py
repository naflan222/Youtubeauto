"""Authorization-only behavior, without Google credentials or a phone."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from requests.exceptions import HTTPError
from tools import authorize
from shorts.oauth import SCOPES

CHANNEL = 'UC' + 'a' * 22


def setup_helper(monkeypatch, tmp_path, extra=()):
    client = tmp_path / 'client.json'
    client.write_text(json.dumps({'installed': {'client_id': 'test-id', 'client_secret': 'test-secret'}}))
    output = tmp_path / 'secrets.txt'
    monkeypatch.setattr('sys.argv', ['authorize', '--client', str(client), '--expected-channel', CHANNEL, '--output', str(output), *extra])
    credentials = SimpleNamespace(refresh_token='test-refresh', client_id='test-id', client_secret='test-secret')
    flow = Mock()
    flow.run_local_server.return_value = credentials
    factory = Mock(return_value=flow)
    monkeypatch.setattr(authorize.InstalledAppFlow, 'from_client_config', factory)
    response = Mock()
    response.json.return_value = {'items': [{'id': CHANNEL, 'snippet': {'title': 'Test Channel'}}]}
    session = Mock()
    session.get.return_value = response
    context = Mock()
    context.__enter__ = Mock(return_value=session)
    context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(authorize, 'AuthorizedSession', Mock(return_value=context))
    monkeypatch.setattr(authorize.shutil, 'which', lambda _: None)
    return output, flow, response, session, factory, client


def test_mobile_manual_consent_checks_channel_and_saves_privately(monkeypatch, tmp_path, capsys):
    output, flow, _, session, factory, _ = setup_helper(monkeypatch, tmp_path, ['--manual-browser'])
    authorize.main()
    options = flow.run_local_server.call_args.kwargs
    assert options['open_browser'] is False
    assert options['host'] == options['bind_addr'] == '127.0.0.1'
    assert options['port'] == 0 and options['timeout_seconds'] == 600
    assert options['access_type'] == 'offline'
    assert factory.call_args.args[1] == SCOPES
    assert session.get.call_args.args[0] == 'https://www.googleapis.com/youtube/v3/channels'
    assert session.get.call_args.kwargs['timeout'] == 30
    assert output.read_text() == 'YOUTUBE_CLIENT_ID=test-id\nYOUTUBE_CLIENT_SECRET=test-secret\nYOUTUBE_REFRESH_TOKEN=test-refresh\n'
    if os.name == 'posix':
        assert output.stat().st_mode & 0o777 == 0o600
    printed = capsys.readouterr().out
    assert 'Test Channel' in printed
    assert 'test-secret' not in printed and 'test-refresh' not in printed


def test_wrong_channel_never_writes_secrets(monkeypatch, tmp_path):
    output, _, response, *_ = setup_helper(monkeypatch, tmp_path)
    response.json.return_value = {'items': [{'id': 'UC' + 'b' * 22, 'snippet': {'title': 'Wrong'}}]}
    with pytest.raises(SystemExit, match='Wrong channel'):
        authorize.main()
    assert not output.exists()


def test_existing_secret_file_is_preserved(monkeypatch, tmp_path):
    output, flow, *_ = setup_helper(monkeypatch, tmp_path)
    output.write_text('do not overwrite')
    with pytest.raises(SystemExit, match='Output exists'):
        authorize.main()
    assert output.read_text() == 'do not overwrite'
    flow.run_local_server.assert_not_called()


def test_absent_offline_token_never_writes_secrets(monkeypatch, tmp_path):
    output, flow, *_ = setup_helper(monkeypatch, tmp_path)
    flow.run_local_server.return_value.refresh_token = None
    with pytest.raises(SystemExit, match='No offline refresh token'):
        authorize.main()
    assert not output.exists()


def test_non_desktop_client_is_rejected_before_consent(monkeypatch, tmp_path):
    output, flow, _, _, _, client = setup_helper(monkeypatch, tmp_path)
    client.write_text(json.dumps({'web': {'client_id': 'test'}}))
    with pytest.raises(SystemExit, match='Desktop app'):
        authorize.main()
    flow.run_local_server.assert_not_called()
    assert not output.exists()


def test_oauth_and_api_errors_do_not_disclose_details(monkeypatch, tmp_path, capsys):
    output, flow, response, *_ = setup_helper(monkeypatch, tmp_path)
    response.raise_for_status.side_effect = HTTPError('private request details')
    with pytest.raises(SystemExit, match='channel lookup failed') as error:
        authorize.main()
    assert 'private request details' not in str(error.value)
    assert not output.exists()
    response.raise_for_status.side_effect = None
    flow.run_local_server.side_effect = ValueError('secret callback details')
    with pytest.raises(SystemExit, match='Consent did not complete') as error:
        authorize.main()
    assert 'secret callback details' not in str(error.value)
    assert 'secret callback details' not in capsys.readouterr().out
    assert not output.exists()


def test_termux_browser_is_external_and_manual_flag_does_not_launch(monkeypatch):
    monkeypatch.setattr(authorize.shutil, 'which', lambda _: '/data/data/com.termux/files/usr/bin/termux-open-url')
    register = Mock()
    monkeypatch.setattr(authorize.webbrowser, 'register', register)
    authorize.configure_browser(manual=True)
    register.assert_not_called()
    authorize.configure_browser(manual=False)
    browser = register.call_args.args[2]
    assert browser.name.endswith('/termux-open-url')
    assert register.call_args.kwargs['preferred'] is True


def test_oauth_lock_is_a_subset_of_runtime_dependencies():
    def entries(path):
        return {line for line in Path(path).read_text().splitlines() if line and not line.startswith('#')}
    assert entries('requirements-oauth.txt') <= entries('requirements.lock')
