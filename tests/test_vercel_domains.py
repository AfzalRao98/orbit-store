import importlib.util
import io
import pathlib
import subprocess
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'verify_vercel_domains.py'
spec = importlib.util.spec_from_file_location('verify_vercel_domains', SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

PROJECT = {
    'name': 'orbit-store',
    'domain': 'orbit-store-omega.vercel.app',
    'project_id': 'prj_example',
    'branch': 'main',
}
SHA = 'a' * 40
DEPLOYMENT = 'dpl_example'


def alias(deployment_id=DEPLOYMENT, project_id='prj_example', redirect=None):
    return {'alias': PROJECT['domain'], 'projectId': project_id, 'deploymentId': deployment_id, 'redirect': redirect}


def deployment(sha=SHA, ready='READY', ref='main', project_id='prj_example', repo_id='1417169167', provider='github', target: str | None = 'production'):
    return {
        'id': DEPLOYMENT,
        'projectId': project_id,
        'name': PROJECT['name'],
        'readyState': ready,
        'target': target,
        'gitSource': {'sha': sha, 'ref': ref, 'type': provider, 'repoId': repo_id},
    }


class MappingTests(unittest.TestCase):
    def check(self, responses):
        calls = []

        def fetch(path, token):
            self.assertEqual(token, 'test-only-token')
            calls.append(path)
            return responses.pop(0)

        result = verifier.verify_mapping(PROJECT, SHA, 'test-only-token', fetch)
        return calls, result

    def test_reads_alias_deployment_then_alias_again(self):
        calls, result = self.check([alias(), deployment(), alias()])
        self.assertEqual(calls, [
            '/v4/aliases/orbit-store-omega.vercel.app',
            '/v13/deployments/dpl_example?withGitRepoInfo=true',
            '/v4/aliases/orbit-store-omega.vercel.app',
        ])
        self.assertEqual(result['sha'], SHA)
        self.assertEqual(result['deployment_id'], DEPLOYMENT)
        self.assertNotIn('token', result)

    def test_rejects_another_project_alias(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'project'):
            self.check([alias(project_id='prj_other')])

    def test_rejects_redirecting_alias(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'redirect'):
            self.check([alias(redirect='other.example')])

    def test_rejects_unready_deployment(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'READY'):
            self.check([alias(), deployment(ready='BUILDING')])

    def test_rejects_preview_target_even_with_same_sha(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'production target'):
            self.check([alias(), deployment(target='preview')])

    def test_rejects_missing_target(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'production target'):
            self.check([alias(), deployment(target=None)])

    def test_rejects_wrong_commit(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'commit'):
            self.check([alias(), deployment(sha='b' * 40)])

    def test_rejects_wrong_branch(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'branch'):
            self.check([alias(), deployment(ref='feature')])

    def test_rejects_wrong_repository(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'repository'):
            self.check([alias(), deployment(repo_id='999')])

    def test_rejects_missing_repository(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'repository'):
            self.check([alias(), deployment(repo_id=None)])

    def test_rejects_non_github_source(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'repository'):
            self.check([alias(), deployment(provider='gitlab')])

    def test_rejects_missing_commit_instead_of_guessing(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'commit'):
            self.check([alias(), deployment(sha=None)])

    def test_rejects_deployment_project_mismatch(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'project'):
            self.check([alias(), deployment(project_id='prj_other')])

    def test_rejects_alias_change_during_verification(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'changed'):
            self.check([alias(), deployment(), alias(deployment_id='dpl_new')])

    def test_rejects_alias_project_change_on_second_read(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'changed'):
            self.check([alias(), deployment(), alias(project_id='prj_other')])

    def test_rejects_redirect_added_on_second_read(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'changed'):
            self.check([alias(), deployment(), alias(redirect='other.example')])

    def test_rejects_remote_ref_change(self):
        with self.assertRaisesRegex(verifier.VerificationError, 'remote Git ref'):
            verifier.require_remote_sha(SHA, 'b' * 40)

    def test_remote_ref_timeout_fails_closed(self):
        with patch.object(verifier.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['git'], 20)):
            with self.assertRaisesRegex(verifier.VerificationError, 'timed out'):
                verifier.current_git_sha('staging')


class TransportAndStorageTests(unittest.TestCase):
    def test_transport_sends_get_to_fixed_origin_without_following_redirects(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(b'{"ok": true}')
        with patch.object(verifier.urllib.request, 'build_opener', return_value=opener) as build:
            result = verifier.fetch_json('/v4/aliases/orbit-store-omega.vercel.app', 'test-only-token')
        self.assertEqual(result, {'ok': True})
        self.assertIs(build.call_args.args[0], verifier.NoRedirect)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertEqual(request.full_url, 'https://api.vercel.com/v4/aliases/orbit-store-omega.vercel.app')

    def test_access_denied_has_no_token_in_error(self):
        opener = Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            'https://api.vercel.com/v4/aliases/orbit-store-omega.vercel.app', 403,
            'test-only-token', {}, None,
        )
        with patch.object(verifier.urllib.request, 'build_opener', return_value=opener):
            with self.assertRaises(verifier.VerificationError) as caught:
                verifier.fetch_json('/v4/aliases/orbit-store-omega.vercel.app', 'test-only-token')
        self.assertIn('HTTP 403', str(caught.exception))
        self.assertNotIn('test-only-token', str(caught.exception))

    def test_local_password_dialog_stores_only_after_successful_access(self):
        keyring = Mock()
        keyring.COLLECTION_DEFAULT = 'default'
        keyring.password_store_sync.return_value = True
        output = io.StringIO()
        with patch.object(verifier.shutil, 'which', return_value='/usr/bin/zenity'), \
             patch.object(verifier.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'test-only-token\n', '')), \
             patch.object(verifier, 'current_git_sha', return_value=SHA), \
             patch.object(verifier, 'verify_mapping', return_value={'domain': PROJECT['domain']}), \
             patch.object(verifier, 'secret_schema', return_value=(keyring, 'schema')), \
             redirect_stdout(output):
            verifier.store_token('orbit-store')
        self.assertEqual(keyring.password_store_sync.call_args.args[4], 'test-only-token')
        self.assertNotIn('test-only-token', output.getvalue())

    def test_denied_access_does_not_store_password(self):
        keyring = Mock()
        with patch.object(verifier.shutil, 'which', return_value='/usr/bin/zenity'), \
             patch.object(verifier.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'test-only-token\n', '')), \
             patch.object(verifier, 'current_git_sha', return_value=SHA), \
             patch.object(verifier, 'verify_mapping', side_effect=verifier.VerificationError('HTTP 403')), \
             patch.object(verifier, 'secret_schema', return_value=(keyring, 'schema')):
            with self.assertRaisesRegex(verifier.VerificationError, 'HTTP 403'):
                verifier.store_token('orbit-store')
        keyring.password_store_sync.assert_not_called()


if __name__ == '__main__':
    unittest.main()
