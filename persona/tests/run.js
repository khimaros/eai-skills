// end-to-end test for persona/scripts/index.html.
// loads the built webview script under a localStorage + document shim and
// drives the dispatcher through the same `ai_edge_gallery_get_result` entry
// point the gallery uses. exits non-zero on any failed assertion.

const fs = require('fs');
const path = require('path');

const INDEX = path.join(__dirname, '..', 'scripts', 'index.html');
const html = fs.readFileSync(INDEX, 'utf8');

const defaultsJson = html.match(
    /id="persona-default-traits">([\s\S]*?)<\/script>/,
)[1];
const scriptBodies = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(
    (m) => m[1],
);
if (scriptBodies.length !== 1) {
    throw new Error(`expected exactly one <script> body, got ${scriptBodies.length}`);
}

const store = new Map();
global.localStorage = {
    get length() { return store.size; },
    key(i) { return [...store.keys()][i]; },
    getItem(k) { return store.has(k) ? store.get(k) : null; },
    setItem(k, v) { store.set(k, String(v)); },
    removeItem(k) { store.delete(k); },
    clear() { store.clear(); },
};
global.document = { getElementById: () => ({ textContent: defaultsJson }) };
global.window = {};

eval(scriptBodies[0]);

const call = async (payload) => {
    const raw = await window.ai_edge_gallery_get_result(JSON.stringify(payload));
    return JSON.parse(raw);
};

let failed = 0;
const check = (label, cond, detail) => {
    if (cond) {
        console.log(`  ok  ${label}`);
    } else {
        failed += 1;
        console.log(`  FAIL ${label}${detail ? ` — ${detail}` : ''}`);
    }
};

const EXPECTED_DEFAULTS = ['BOOTSTRAP.md', 'IDENTITY.md', 'SOUL.md', 'VOICE.md'];

(async () => {
    console.log('cold bootstrap seeds defaults');
    let r = await call({ action: 'persona_bootstrap' });
    check('result present', !!r.result, JSON.stringify(r));
    check(
        'returns all default traits',
        EXPECTED_DEFAULTS.every((n) => n in (r.result?.traits || {})),
        `got ${Object.keys(r.result?.traits || {}).join(',')}`,
    );
    check('prompt non-empty', (r.result?.prompt || '').length > 100);
    check('available is array', Array.isArray(r.result?.available));

    console.log('trait roundtrip');
    await call({ action: 'trait_write', name: 'mood.md', content: '# mood\nbright' });
    r = await call({ action: 'trait_read', name: 'mood.md' });
    check('read returns content', r.result?.content === '# mood\nbright');
    r = await call({ action: 'persona_bootstrap' });
    check('lowercase trait surfaces in available', (r.result?.available || []).includes('mood.md'));

    console.log('data roundtrip');
    await call({ action: 'data_write', key: 'count', value: 7 });
    r = await call({ action: 'data_read', key: 'count' });
    check('data_read returns value', r.result?.value === 7);
    r = await call({ action: 'data_query', values: true });
    check('data_query with values', r.result?.entries?.some((e) => e.key === 'count' && e.value === 7));

    console.log('hook register + call');
    r = await call({
        action: 'hook_register',
        name: 'echo',
        description: 'echo input back',
        body: 'return { echoed: input };',
    });
    check('hook registered', r.result?.name === 'echo');
    r = await call({ action: 'echo', hello: 'world' });
    check('hook called by action name', r.result?.echoed?.hello === 'world');

    console.log('safeRead skips corrupt entries');
    localStorage.setItem('persona:hook:broken', '{not json');
    r = await call({ action: 'hook_list' });
    check('hook_list survives bad json', Array.isArray(r.result?.hooks));
    check('hook_list still includes good hook', r.result.hooks.some((h) => h.name === 'echo'));
    localStorage.setItem('persona:data:broken', '{not json');
    r = await call({ action: 'data_query', values: true });
    check('data_query survives bad json', Array.isArray(r.result?.entries));

    console.log('persona_reset wipes everything');
    r = await call({ action: 'persona_reset' });
    check('reset returns count', typeof r.result?.deleted === 'number' && r.result.deleted > 0);
    check('store empty after reset', store.size === 0);

    console.log('bootstrap after reset re-seeds');
    r = await call({ action: 'persona_bootstrap' });
    check(
        're-seeded all defaults',
        EXPECTED_DEFAULTS.every((n) => n in (r.result?.traits || {})),
    );

    console.log('errors are reported, not thrown');
    r = await call({ action: 'no_such_action' });
    check('unknown action returns error', !!r.error && !r.result);

    if (failed) {
        console.log(`\n${failed} check(s) failed`);
        process.exit(1);
    }
    console.log('\nall checks passed');
})().catch((e) => {
    console.error('test crashed:', e);
    process.exit(1);
});
