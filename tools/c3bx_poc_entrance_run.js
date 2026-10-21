// C3-BX: THZ3 walk-on series (and any zone) through the P4 source, optionally with an in-memory candidate patch set (tools/c3bx_candidates.js). Same scenario and columns as tools/t3_poc_boss_run.js.
//   POC=<P4 checkout> [C3BX_PATCH=B1] node tools/c3bx_poc_entrance_run.js [--write|--check]       (data/c3bx/poc-entrance-<set>.json, THZ3 only)
const fs = require('fs'), path = require('path');
const POC = process.env.POC || path.resolve(__dirname, '../..');
const PATCH = (process.env.C3BX_PATCH || '').split(',').filter(Boolean);
require('./c3bx_candidates.js').install(PATCH, POC);
const T3 = require('./t3_poc_boss_run.js');
const OUT = process.env.C3BX_OUT ? path.resolve(process.env.C3BX_OUT) : path.resolve(__dirname, '..', 'data', 'c3bx', 'poc-entrance-' + (PATCH.join('+') || 'p4') + '.json');
const WIDTHS = [[256, 192], [348, 196], [400, 225]];
const ZONES = (process.env.C3BX_ZONES || 'THZ3').split(',');
function build() {
    const zones = {};
    for (const z of ZONES) { zones[z] = {}; for (const [w, h] of WIDTHS) { zones[z]['w' + w] = {view: [w, h]}; for (const sc of ['hold', 'stop']) zones[z]['w' + w][sc] = T3.run(z, w, h, sc); } }
    return {description: PATCH.length ? 'PROPOSAL MODEL entrance series: P4 source + in-memory patches ' + PATCH.join('+') : 'POC-SOURCE MODEL entrance series (shipped P4 GML)', patches: PATCH, updates: T3.FRAMES, zones};
}
const text = JSON.stringify(build()) + '\n';
if (process.argv.includes('--write')) { fs.mkdirSync(path.dirname(OUT), {recursive: true}); fs.writeFileSync(OUT, text); console.log('wrote', OUT, text.length); }
else if (process.argv.includes('--check')) { const same = fs.existsSync(OUT) && fs.readFileSync(OUT, 'utf8') === text; console.log('CHECK entrance series', same ? 'identical' : 'DIFFERENT'); process.exit(same ? 0 : 1); }
else process.stdout.write(text);
