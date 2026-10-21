// C3-BX: READ-ONLY execution of the P4 POC source (shipped GML in the POC's own node VM harness) for the boss EXIT: defeat -> clear release -> player state $20 run-off -> act-clear flag.
// Evidence class: POC-SOURCE MODEL (node VM, shipped GML); not GameMaker, not Windows. The POC checkout is never modified.
//
//   POC=<P4 checkout> node tools/c3bx_poc_exit_run.js [--write|--check]            (data/c3bx/poc-exit-p4.json)
//   POC=<P4 checkout> C3BX_PATCH=A1,A2 node tools/c3bx_poc_exit_run.js [--write|--check]  (data/c3bx/poc-exit-A1+A2.json: PROPOSAL MODEL, in-memory text patches only)
//
// Scenario (identical for every zone and width): the shipped entrance runs with RIGHT held (the T3 'hold' convention) until the arena camera is settled and the boss is in its
// fight state; Sonic is then placed on the floor at the arena camera + 73 (the screen X Sonic has in the ROM AQZ3 exit trace: data/rom-cache/aqz/boss-59-game-checks.json,
// world 1800 at camera 1727), speed 0, floor bit set; the zone's own clear routine is called (the release the ROM runs at $81BD / $9D26); RIGHT is NOT held afterwards
// (state $20 runs by itself). Rows are per update (host.frame + the Step_2 camera passes).
//
// CANDIDATES: C3BX_PATCH=A1,A2 applies the in-memory source patches of tools/c3bx_candidates.js (evidence class PROPOSAL MODEL: P4 source + the stated text patch, never the POC checkout).
const fs = require('fs'), path = require('path');
const POC = process.env.POC || path.resolve(__dirname, '../..');
const PATCH = (process.env.C3BX_PATCH || '').split(',').filter(Boolean);
require('./c3bx_candidates.js').install(PATCH, POC);         // must precede the harness load: the harness reads the GML text when a world is built
const T3 = require('./t3_poc_boss_run.js');
const OUT_NAME = PATCH.length ? 'poc-exit-' + PATCH.join('+') + '.json' : 'poc-exit-p4.json';
const OUT = process.env.C3BX_OUT ? path.resolve(process.env.C3BX_OUT) : path.resolve(__dirname, '..', 'data', 'c3bx', OUT_NAME);
const WIDTHS = process.env.T3_WIDTHS ? process.env.T3_WIDTHS.split(',').map(x => x.split('x').map(Number)) : [[256, 192], [348, 196], [400, 225]];
const SCREEN0 = 73;      // Sonic's screen X at the clear in the ROM AQZ3 exit trace
const SCREEN0_ZONE = {GPZ3: 97};   // GPZ3: the natural ROM fight (data/rom-cache/gpz/boss-51-fullgame.json) releases with Sonic at world 1760 = screen 97; the POC run matches it so the two are comparable
const MAXU = 700;

function settled(zone, S, hist) {
    const s = S.sample();
    if (zone === 'THZ3') return s.bs === 6 && s.mode === 3;
    if (zone === 'GPZ3') return s.mode === 3 && s.bs >= 7;
    return s.mode === 3 && hist.length > 30 && hist.slice(-30).every(x => x === hist[hist.length - 1]);
}

function inject(zone, S) {
    const {c, g, h, w} = S, vp = c.chaos_vp_current(), b = S.ctrl();
    const x = Math.floor(vp.left + (SCREEN0_ZONE[zone] || SCREEN0)), y = Math.floor(S.p.chaosCore.yu / 256);
    // a fresh standing Sonic: the entrance run ends with the hold player hit by the boss, and the exit starts from an ordinary standing player on the floor
    const p = h.newPlayer(x, y, {state: 1, move: 0, bg: 2, contacts: 2});
    S.p = p; g.ring = 20; p.chaosCore.rings = 20;
    const core = p.chaosCore;
    for (const sl of (g.chaosS2 ? g.chaosS2.slots : [])) if (sl && sl.type >= 0x5A && sl.type <= 0x5D) { sl.type = 0; sl.asleep = true; }   // AQZ3: the ROM defeat sequence waits for its children to finish; none is alive at $81BD
    if (zone === 'THZ3') { b.state = 5; b.state_age = 0; }
    else if (zone === 'GPZ3') { for (const sl of b.slots) if (sl !== b.head) sl.type = 0xFF; b.camera_x = vp.left; c.chaos_51_callback(b, b.head, 0x9D26, core, true); }   // the ROM defeat waits for the segments; none is alive at $9D26
    else if (zone === 'SEZ3') { for (const sl of g.chaosS2.slots) if (sl && sl.type === 0x55) sl.type = 0; const s = g.chaosS2.slots.find(q => q.boss && q.type === 0x54); c.chaos_54_clear(b, g.chaosS2, s, core, true, vp); }
    else if (zone === 'MGHZ3') {
        const M3 = c.global.chaosM3, s = M3.slots.find(q => q.boss && q.type === 0x56);
        const call = () => c.chaos_56_callback(b, s, 0x81BD, p.chaosCore, true, c.chaos_vp_current(), -4);   // below the $81BD player gate (WORLD x >= 3356) it only releases the camera; Sonic then walks right (RIGHT held) until the gate opens
        M3.slots[M3.slots.indexOf(s)] = Object.assign({}, s, {type: 0, boss: false});   // the defeated boss body is no longer a hazard; the state-5 callback is driven by hand on the original slot
        call(); S.perUpdate = call;
    } else if (zone === 'AQZ3') { const s = g.chaosS2.slots.find(q => q.boss59 && q.type === 0x59); c.chaos_59_viewport_callback(b, g.chaosS2, s, 0x81BD, core, true, vp); }
    return p;
}

function exitRun(zone, W, H) {
    const S = T3.BUILD[zone](W, H), {h, c, w, p} = S, core = p.chaosCore, hist = [];
    const step = T3.stepOrder;
    let ready = null;
    for (let u = 1; u <= 2200; u++) {
        p.x = Math.floor(core.xu / 256); p.y = Math.floor(core.yu / 256) + 5;
        h.frame({right: true});
        step(c, S);
        hist.push(w.cam.x);
        if (settled(zone, S, hist)) { ready = u; break; }
    }
    if (ready === null) return {error: 'arena never settled'};
    const pp = inject(zone, S), core2 = pp.chaosCore;
    const cols = {}, push = (k, v) => (cols[k] = cols[k] || []).push(typeof v === 'boolean' ? (v ? 1 : 0) : v);
    let cleared = null;
    for (let u = 0; u <= MAXU; u++) {
        if (u > 0) {
            pp.x = Math.floor(core2.xu / 256); pp.y = Math.floor(core2.yu / 256) + 5;
            const walk = zone === 'MGHZ3' && core2.state !== 32 && core2.next !== 32;     // MGHZ3: the clear gate is a player-controlled walk to WORLD x 3356: a scripted 6 px/update walk on the floor (synthetic), no terrain
            if (walk) { core2.xu += 6 * 256; core2.vx = 1536; pp.x = Math.floor(core2.xu / 256); }
            h.frame({right: false}); if (S.perUpdate) S.perUpdate(); step(c, S);
        }
        const b = S.ctrl(), px = Math.floor(core2.xu / 256);
        push('u', u); push('px', px); push('vx', core2.vx); push('st', core2.state); push('nx', core2.next);
        push('cx', w.cam.x); push('cy', w.cam.y); push('scr', px - w.cam.x);
        push('mode', b.camera_mode !== undefined ? b.camera_mode : -1); push('frozen', !!b.frozen); push('clear', !!core2.act_clear);
        if (core2.act_clear && cleared === null) { cleared = u; }
        if (cleared !== null && u >= cleared + 2) break;
    }
    return {ready_u: ready, room_w: w.roomWidth, view: [W, H], cleared_u: cleared, cols};
}

function build() {
    const zones = {};
    for (const zone of ['THZ3', 'GPZ3', 'SEZ3', 'MGHZ3', 'AQZ3']) {
        zones[zone] = {};
        for (const [W, H] of WIDTHS) zones[zone]['w' + W] = exitRun(zone, W, H);
    }
    return {description: PATCH.length ? 'PROPOSAL MODEL exit series: P4 source + in-memory patches ' + PATCH.join('+') : 'POC-SOURCE MODEL exit series (shipped P4 GML, node VM, Step_2 order)',
            evidence: PATCH.length ? 'PROPOSAL MODEL (node VM, P4 GML + the text patches of tools/c3bx_candidates.js); not POC code' : 'POC-SOURCE MODEL (node VM, shipped GML); not GameMaker; not Windows', patches: PATCH,
            screen0: SCREEN0, screen0_zone: SCREEN0_ZONE, widths: WIDTHS.map(x => x.join('x')), zones};
}

if (require.main !== module) { module.exports = {exitRun, build}; return; }
const text = JSON.stringify(build()) + '\n';
if (process.argv.includes('--write')) { fs.mkdirSync(path.dirname(OUT), {recursive: true}); fs.writeFileSync(OUT, text); console.log('wrote', OUT, text.length); }
else if (process.argv.includes('--check')) { const same = fs.existsSync(OUT) && fs.readFileSync(OUT, 'utf8') === text; console.log('CHECK exit series', same ? 'identical' : 'DIFFERENT'); process.exit(same ? 0 : 1); }
else process.stdout.write(text);
