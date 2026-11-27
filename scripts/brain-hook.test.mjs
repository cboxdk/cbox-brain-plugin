import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { delimiter, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const wrapper = fileURLToPath(new URL('../plugins/cbox-brain/scripts/brain-hook.sh', import.meta.url));

function session(t) {
    const home = mkdtempSync(join(tmpdir(), 'brain-plugin-test-'));
    t.after(() => rmSync(home, { recursive: true, force: true }));
    const repo = join(home, 'repo');
    mkdirSync(repo);
    mkdirSync(join(home, 'bin'));
    execFileSync('git', ['init', '-q', repo]);
    const oldCli = join(home, 'bin', 'brain');
    writeFileSync(oldCli, '#!/bin/sh\nprintf "old-cli-feedback\\n"\n', { mode: 0o755 });
    const env = {
        PATH: join(home, 'bin') + delimiter + process.env.PATH,
        BRAIN_TOKEN: 'test-token',
        BRAIN_SERVER: 'http://127.0.0.1:9',
        BRAIN_CACHE_DIR: join(home, 'cache'),
        CBOX_BRAIN_CONFIG: join(home, 'config'),
    };
    return {
        repo, home, oldCli,
        hook: (event, input = {}, extraEnv = {}) => execFileSync('bash', [wrapper, event], {
            env: { ...env, ...extraEnv }, encoding: 'utf8', timeout: 5000,
            input: JSON.stringify({ session_id: 'plugin-session', cwd: repo, ...input }),
        }),
    };
}

test('plugin update uses its bundled hooks even when an older brain is on PATH', (t) => {
    const { hook, repo, home } = session(t);
    assert.equal(hook('pre-tool', { tool_name: 'Write', tool_input: { file_path: join(home, 'scratchpad/bench.js') } }), '');
    assert.equal(hook('stop'), '');
    const output = JSON.parse(hook('pre-tool', { tool_name: 'Write', tool_input: { file_path: join(repo, 'new/file.js') } })).hookSpecificOutput;
    assert.equal(output.hookEventName, 'PreToolUse');
    assert.match(output.additionalContext, /brain_handoff/);
    assert.equal(hook('stop'), '');
});

test('Stop stays silent even with an explicitly selected older CLI; other events respect the override', (t) => {
    const { hook, oldCli } = session(t);
    assert.equal(hook('stop', {}, { BRAIN_CLI: oldCli }), '');
    assert.equal(hook('pre-tool', {}, { BRAIN_CLI: oldCli }), 'old-cli-feedback\n');
});

test('plugin wrapper delivers the learning reminder once on the ninth call, never at Stop', (t) => {
    const { hook } = session(t);
    const input = { tool_name: 'Bash', tool_input: { command: 'ls' } };
    for (let i = 0; i < 8; i++) assert.equal(hook('pre-tool', input), '');
    const output = JSON.parse(hook('pre-tool', input)).hookSpecificOutput;
    assert.equal(output.hookEventName, 'PreToolUse');
    assert.match(output.additionalContext, /9 tool calls and remembered nothing/);
    assert.equal(hook('pre-tool', input), '');
    assert.equal(hook('stop'), '');
    assert.equal(hook('pre-tool', input, { BRAIN_HOOKS: 'off' }), '');
});
