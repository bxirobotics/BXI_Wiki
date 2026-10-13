const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const { join } = require('node:path');
const source = readFileSync(join(__dirname, '../docs/javascripts/locale-preference.js'), 'utf8');

function visit(pathname, timeZone, cookie = '') {
  let target;
  let click;
  const document = { cookie, addEventListener: (event, callback) => { click = callback; } };
  runInNewContext(source, {
    document,
    location: { pathname, search: '?ref=test', hash: '#setup', replace: value => { target = value; } },
    Intl: { DateTimeFormat: () => ({ resolvedOptions: () => ({ timeZone }) }) },
  });
  return { target, document, click };
}

test('China timezones select Chinese while English remains the general default', () => {
  assert.equal(visit('/elf3/overview/', 'Asia/Shanghai').target, '/zh/elf3/overview/?ref=test#setup');
  assert.equal(visit('/elf3/overview/', 'Asia/Singapore').target, undefined);
  assert.equal(visit('/elf3/overview/', undefined).target, undefined);
});

test('explicit Chinese URLs and saved English choices are respected', () => {
  assert.equal(visit('/zh/elf3/overview/', 'America/New_York').target, undefined);
  assert.equal(visit('/elf3/overview/', 'Asia/Shanghai', 'bxi_locale=en').target, undefined);
  assert.equal(visit('/elf3/overview/', 'UTC', 'bxi_locale=zh').target, '/zh/elf3/overview/?ref=test#setup');
});

test('language menu clicks persist a choice before navigation', () => {
  const result = visit('/zh/elf3/overview/', 'Asia/Shanghai');
  result.click({ target: { closest: () => ({ getAttribute: () => 'en' }) } });
  assert.match(result.document.cookie, /^bxi_locale=en;/);
});
