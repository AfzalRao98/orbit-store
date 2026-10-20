#!/usr/bin/python3
"""Read-only proof that Orbit's configured Vercel domains serve current Git heads.

Tokens live in the current user's GNOME Keyring, never in this repository.
Only HTTPS GET requests are sent to api.vercel.com. No deployment operation exists.
"""

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

PROJECTS = {
    'orbit-store-stagging': {
        'name': 'orbit-store-stagging',
        'domain': 'orbit-store-stagging.vercel.app',
        'project_id': 'prj_djpQg7diy6vrHrKFtIvdUKfQHiEq',
        'branch': 'staging',
    },
    'orbit-store': {
        'name': 'orbit-store',
        'domain': 'orbit-store-omega.vercel.app',
        'project_id': 'prj_Jw6RHtJdL38s1NjMQGSEZpMQ7qcg',
        'branch': 'main',
    },
}
REPO = pathlib.Path(__file__).resolve().parents[1]
SHA_PATTERN = re.compile(r'[0-9a-f]{40}\Z')
DEPLOYMENT_PATTERN = re.compile(r'dpl_[A-Za-z0-9]+\Z')
GITHUB_REPO_ID = '1417169167'  # AfzalRao98/orbit-store (GitHub REST repository ID)


class VerificationError(Exception):
    """Expected, sanitized failure of a verification gate."""


def verify_mapping(project, expected_sha, token, fetch):
    """Verify alias -> deployment -> alias, failing closed on missing fields."""
    if not SHA_PATTERN.fullmatch(expected_sha):
        raise VerificationError('expected commit is not a full Git SHA')
    alias_path = '/v4/aliases/' + project['domain']
    first = fetch(alias_path, token)
    if first.get('alias') != project['domain'] or first.get('projectId') != project['project_id']:
        raise VerificationError('alias hostname or project did not match')
    if first.get('redirect'):
        raise VerificationError('alias redirects rather than serving this deployment')
    deployment_id = first.get('deploymentId')
    if not isinstance(deployment_id, str) or not DEPLOYMENT_PATTERN.fullmatch(deployment_id):
        raise VerificationError('alias has no valid deployment ID')

    detail = fetch('/v13/deployments/' + deployment_id + '?withGitRepoInfo=true', token)
    if detail.get('id') != deployment_id:
        raise VerificationError('deployment ID did not match alias')
    if detail.get('projectId') != project['project_id'] or detail.get('name') != project['name']:
        raise VerificationError('deployment project did not match alias and expected project')
    if detail.get('readyState') != 'READY':
        raise VerificationError('deployment is not READY')
    if detail.get('target') != 'production':
        raise VerificationError('deployment is not the production target for this Vercel project')
    source = detail.get('gitSource') or {}
    if source.get('type') != 'github' or str(source.get('repoId')) != GITHUB_REPO_ID:
        raise VerificationError('deployment Git repository did not match')
    if source.get('sha') != expected_sha:
        raise VerificationError('deployment commit does not match current Git ref')
    if source.get('ref') not in (project['branch'], 'refs/heads/' + project['branch']):
        raise VerificationError('deployment Git branch did not match')

    second = fetch(alias_path, token)
    if second.get('redirect'):
        raise VerificationError('alias changed to a redirect during verification')
    if any(second.get(key) != first.get(key) for key in ('alias', 'projectId', 'deploymentId')):
        raise VerificationError('alias changed during verification')
    return {
        'domain': project['domain'],
        'project': project['name'],
        'project_id': project['project_id'],
        'deployment_id': deployment_id,
        'branch': project['branch'],
        'github_repo_id': GITHUB_REPO_ID,
        'sha': expected_sha,
        'readiness': 'READY',
        'target': 'production',
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def fetch_json(path, token):
    # A fixed API origin and validated paths prevent redirect or response-controlled exfiltration.
    if not (path.startswith('/v4/aliases/') or path.startswith('/v13/deployments/')):
        raise VerificationError('unexpected Vercel API endpoint')
    request = urllib.request.Request(
        'https://api.vercel.com' + path,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'},
        method='GET',
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise VerificationError(f'Vercel GET returned HTTP {exc.code}; check token scope, expiry and project access (no automatic permission widening)') from None
        raise VerificationError(f'Vercel GET returned HTTP {exc.code}') from None
    except (urllib.error.URLError, TimeoutError):
        raise VerificationError('Vercel GET failed due to network or timeout') from None
    except (ValueError, UnicodeError, TypeError):
        raise VerificationError('Vercel GET did not return usable JSON') from None


def current_git_sha(branch):
    try:
        result = subprocess.run(
            ['git', 'ls-remote', 'origin', 'refs/heads/' + branch],
            cwd=REPO, text=True, capture_output=True, check=False, timeout=20,
        )
    except subprocess.TimeoutExpired:
        raise VerificationError('remote Git ref lookup timed out') from None
    if result.returncode or not result.stdout.strip():
        raise VerificationError('cannot read current remote Git ref for ' + branch)
    line = result.stdout.strip().split('\n')
    if len(line) != 1:
        raise VerificationError('remote Git ref is ambiguous for ' + branch)
    sha, ref = line[0].split('\t', 1)
    if ref != 'refs/heads/' + branch or not SHA_PATTERN.fullmatch(sha):
        raise VerificationError('remote Git ref is invalid for ' + branch)
    return sha


def require_remote_sha(expected, current):
    if not SHA_PATTERN.fullmatch(expected):
        raise VerificationError('recorded expected commit is not a full Git SHA')
    if current != expected:
        raise VerificationError('remote Git ref no longer matches the recorded merge SHA')


def secret_schema():
    import gi
    gi.require_version('Secret', '1')
    from gi.repository import Secret
    schema = Secret.Schema.new(
        'com.orbit.vercel-domain-verification', Secret.SchemaFlags.NONE,
        {'project': Secret.SchemaAttributeType.STRING},
    )
    return Secret, schema


def load_token(project_name):
    Secret, schema = secret_schema()
    token = Secret.password_lookup_sync(schema, {'project': project_name}, None)
    if not token:
        raise VerificationError('no GNOME Keyring token stored for ' + project_name)
    return token


def store_token(project_name):
    if not shutil.which('zenity'):
        raise VerificationError('zenity is needed for a private local password dialog')
    result = subprocess.run(
        ['zenity', '--password', '--title=Orbit Vercel token: ' + project_name,
         '--text=Paste the project-scoped Vercel access token here. It will not be printed or saved in the repository.'],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise VerificationError('token entry was canceled; nothing was stored')
    token = result.stdout.rstrip('\r\n')
    if not token:
        raise VerificationError('empty token; nothing was stored')
    project = PROJECTS[project_name]
    verified = verify_mapping(project, current_git_sha(project['branch']), token, fetch_json)
    Secret, schema = secret_schema()
    saved = Secret.password_store_sync(
        schema, {'project': project_name}, Secret.COLLECTION_DEFAULT,
        'Orbit Vercel domain verification: ' + project_name, token, None,
    )
    if not saved:
        raise VerificationError('GNOME Keyring did not confirm storage')
    print(json.dumps({'stored_in': 'GNOME Keyring', 'verified': verified}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store-token', choices=PROJECTS, help='open a local hidden-entry dialog and store one scoped token')
    parser.add_argument('--project', choices=PROJECTS, help='project whose domain is being verified')
    parser.add_argument('--expected-sha', help='the exact, recorded full staging/main merge SHA (required for a release check)')
    args = parser.parse_args()
    if args.store_token and (args.project or args.expected_sha):
        parser.error('--store-token cannot be combined with --project or --expected-sha')
    if not args.store_token and (not args.project or not args.expected_sha):
        parser.error('a release check requires both --project and --expected-sha')
    try:
        if args.store_token:
            store_token(args.store_token)
            return 0
        project = PROJECTS[args.project]
        require_remote_sha(args.expected_sha, current_git_sha(project['branch']))
        result = verify_mapping(project, args.expected_sha, load_token(args.project), fetch_json)
        print(json.dumps({'verified': result}, sort_keys=True))
        return 0
    except VerificationError as exc:
        print('Verification failed: ' + str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        # Never print exception context: a library error could contain a credential.
        print('Verification failed: local credential or API error (' + type(exc).__name__ + ')', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
