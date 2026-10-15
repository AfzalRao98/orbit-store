import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {test} from 'node:test';

const workflow = readFileSync(new URL('../.github/workflows/ci.yml', import.meta.url), 'utf8');

for (const event of ['pull_request', 'push']) {
  test(`Store checks runs for ${event} on main and staging`, () => {
    assert.match(workflow, new RegExp(`^  ${event}:\\n    branches: \\[main, staging\\]$`, 'm'));
  });
}

test('Store checks retains install, tests, and build', () => {
  assert.match(workflow, /^      - run: npm ci$/m);
  assert.match(workflow, /^      - run: npm test$/m);
  assert.match(workflow, /^      - run: npm run build$/m);
});
