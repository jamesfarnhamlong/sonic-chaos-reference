// T3: READ-ONLY execution of the accepted POC source (shipped GML in the POC's own node VM harness) for the six boss arrivals at 256 and 348 px.
// Evidence class: POC-SOURCE MODEL (node VM, shipped GML). This is not GameMaker and not Windows: it proves what the shipped functions compute when driven in the
// documented order, nothing more. The POC checkout is never modified.
//
//   POC=<path to a SonicChaos_POC checkout> node tools/t3_poc_boss_run.js [--write|--check]
//
// Frame order (OBJ_chaos_zone Step_2): host.frame (player adapter step/end + objects phase), then chaos_camera_ordinary_step() when
// chaos_camera_follow_allowed(), then chaos_goal_camera_step(), chaos_boss_camera_step(), chaos_51_/56_/54_camera_step(), chaos_eez_boss_camera_step(),
// chaos_59_camera_step(). The zone End Step's AQZ/EEZ view clamps are not part of the model (they only bound the world edge, never the arena).
//
// Scenarios (Sonic starts on the act floor BACK px left of the boss placement, state 1, RIGHT held):
//   hold = RIGHT held for the whole run (a player who keeps running through the intro; the T2 convention)
//   stop = RIGHT released at the first update the boss camera owner reports mode >= 2 (a player who waits at the trigger)
// Widths: 256x192 (control) and 348x196 (the shipped wide view). Rows are per update (one host.frame + camera pass).
const fs = require('fs'), path = require('path'), cp = require('child_process');
const POC = process.env.POC || 'E:/AI/Codex/Sonic Chaos/SonicChaos_POC_c1i';
const {loadHost} = require(path.join(POC, 'verification/chaos_world_harness.js'));
const OUT = path.resolve(__dirname, '..', 'data', 't3', 'poc-series.json');
const FRAMES = 450;
const WIDTHS = [[256, 192], [348, 196]];
const BACK = {THZ3: 376, GPZ3: 480, SEZ3: 480, MGHZ3: 480, AQZ3: 480, EEZ3: 260};   // THZ3: the act floor starts at X 1480 (T2), so the run starts at 1560

function common(h, roomName, rw, rh, x0, camY, viewW, viewH) {
    const c = h.ctx, g = h.g, w = h.world;
    c.room = c['ROM_chaos_' + roomName];
    w.roomWidth = rw; w.roomHeight = rh; w.follow = false;
    const lead = viewW === 256 ? 104 : Math.floor(viewW / 2) - 24;
    w.cam = {x: x0 - lead, y: camY, w: viewW, h: viewH};
    c.__view_get = () => viewH;
    c.show_error = m => { throw Error(m); };
    c.chaos_level_install_layout();
    g.chaosPan = c.chaos_goal_pan_new(); g.chaosCamLeft = 0; g.chaosGoalContact = false; g.chaosComplete = false; g.chaosDebugSession = true;
    g.chaosLostRings = []; g.chaosBossNextAct = -4; g.chaosHudSlide = 0; g.chaosCrushDeathPhase = 0; g.minutes = 0; g.seconds = 0; g.ring = 0; g.chaosFinishTime = 0;
    return {c, g, w};
}

/// Each builder returns {h, c, g, w, p, sample()}; sample() reads the boss controller of the zone (primary slot only, plus the AQZ $5A child and the EEZ encounter).
const BUILD = {
    THZ3(viewW, viewH) {
        const h = loadHost(), {c, g, w} = common(h, 'thz3', 2560, 512, 1936 - BACK.THZ3, 80, viewW, viewH);
        const ax = 1936, ay = 238, x0 = ax - BACK.THZ3;
        const p = h.newPlayer(x0, ay, {state: 1, move: 0, bg: 2, contacts: 2});
        const boss = h.create(h.ids.OBJ_chaos_object_50, ax, ay);
        g.chaosCam = c.chaos_cam_new(w.cam.x, w.cam.y, viewW);
        return {h, c, g, w, p, sample: () => { const b = boss.chaosBoss; return {act: b.state !== -1, mode: b.camera_mode, bs: b.state, bx: Math.floor(b.xu / 256), by: b.y, bfr: b.frame, right: b.camera_right, left: b.camera_min}; }};
    },
    GPZ3(viewW, viewH) {
        const h = loadHost(), ax = 1728, ay = 270, x0 = ax - BACK.GPZ3, {c, g, w} = common(h, 'gpz3', 2560, 512, x0, 96, viewW, viewH);
        const p = h.newPlayer(x0, ay, {state: 1, move: 0, bg: 2, contacts: 2});
        const boss = h.create(h.ids.OBJ_chaos_object_51, ax, ay);
        g.chaosCam = c.chaos_cam_new(w.cam.x, w.cam.y, viewW);
        return {h, c, g, w, p, sample: () => { const b = boss.chaosBoss51, s = b.head; return {act: b.active, mode: b.camera_mode, bs: s.state, bx: Math.floor(s.xu / 256), by: Math.floor(s.yu / 256), bfr: s.frame, right: b.camera_right, left: b.camera_left}; }};
    },
    SEZ3(viewW, viewH) {
        const L = require(path.join(POC, 'verification/sez54_lib.js'));
        const h = L.newWorld(viewW, viewH, true), c = h.ctx, g = h.g, ax = 3200, ay = 622, x0 = ax - BACK.SEZ3;
        const {w} = common(h, 'sez3', 4096, 1024, x0, 514, viewW, viewH);
        g.chaosS2 = c.chaos_s2_new(); g.chaosSezEffects = c.chaos_sez_effect_new(); g.chaosSezBossActive = false;
        c.chaos_54_register(c.SCR_chaos_sez3_objects().find(r => r[3] === 0x54));
        const p = h.newPlayer(x0, ay, {state: 1, move: 0, bg: 2, contacts: 2});
        g.chaosCam = c.chaos_cam_new(w.cam.x, w.cam.y, viewW);
        return {h, c, g, w, p, sample: () => {
            const b = g.chaosSez54, s = g.chaosS2.slots.find(q => q.boss && q.type === 0x54);
            return {act: b.active, mode: b.camera_mode, bs: s ? s.state : -1, bx: s ? c.chaos_54_x(s) : null, by: s ? c.chaos_54_y(s) : null, bfr: s ? s.frame : null, right: b.camera_right, left: b.camera_left};
        }};
    },
    MGHZ3(viewW, viewH) {
        const L = require(path.join(POC, 'verification/mghz_boss_lib.js'));
        const h = L.newWorld(viewW, viewH, true), c = h.ctx, g = h.g, w = h.world;
        c.chaos_level_install_layout();
        g.chaosDebugSession = true; g.zoneGoto = 4; g.chaosComplete = false; g.chaosGoalContact = false;
        const row = c.SCR_chaos_mghz3_objects().find(r => r[3] === 0x56);
        const inst = h.create(c.OBJ_chaos_object_56, row[1], row[2]);
        c.chaos_m3_record(c.global.chaosM3, row, inst);
        const x0 = row[1] - BACK.MGHZ3, lead = viewW === 256 ? 104 : Math.floor(viewW / 2) - 24;
        const p = h.newPlayer(x0, 366, {state: 1, move: 0, bg: 2, contacts: 2});
        w.cam = {x: x0 - lead, y: 303, w: viewW, h: viewH};
        c.global.chaosM3.initial = false;
        g.chaosPan = c.chaos_goal_pan_new(); g.chaosCamLeft = 0; c.__view_get = () => viewH;
        g.chaosCam = c.chaos_cam_new(w.cam.x, w.cam.y, viewW);
        return {h, c, g, w, p, sample: () => {
            const b = inst.chaosBoss56, s = c.global.chaosM3.slots.find(q => q.boss && q.type === 0x56);
            return {act: b.active, mode: b.camera_mode, bs: s ? s.state : -1, bx: s ? c.chaos_56_x(s) : null, by: s ? c.chaos_56_y(s) : null, bfr: s ? s.frame : null, right: b.camera_right, left: b.camera_left};
        }};
    },
    AQZ3(viewW, viewH) {
        const h = loadHost(), c = h.ctx, g = h.g, ax = 1856, ay = 238, x0 = ax - BACK.AQZ3;
        const {w} = common(h, 'aqz3', 2560, 512, x0, 138, viewW, viewH);
        g.chaosS2 = c.chaos_s2_new(); g.chaosAqzEnv = c.chaos_aqz_env_new(3);
        g.chaosAqz59 = undefined; c.chaos_59_register(c.SCR_chaos_aqz3_objects().find(r => r[3] === 0x59));
        const p = h.newPlayer(x0, ay, {state: 1, move: 0, bg: 2, contacts: 2});
        g.chaosCam = c.chaos_cam_new(w.cam.x, w.cam.y, viewW);
        return {h, c, g, w, p, sample: () => {
            const b = g.chaosAqz59, bs = g.chaosS2.slots.filter(q => q.boss59 && q.type >= 0x59 && q.type <= 0x5D);
            const s = bs.find(q => q.type === 0x59) || bs[0], k = bs.find(q => q.type === 0x5A);
            return {act: b.active, mode: b.camera_mode, bs: s ? s.state : -1, bx: s ? c.chaos_59_x(s) : null, by: s ? c.chaos_59_y(s) : null, bfr: s ? s.frame : null, right: b.camera_right, left: b.camera_left,
                    kx: k ? c.chaos_59_view_x(k) : null, ky: k ? c.chaos_59_y(k) : null, kfr: k ? k.frame : null, ready: b.intro_ready ? 1 : 0};
        }};
    },
    EEZ3(viewW, viewH) {
        const h = loadHost(), c = h.ctx, g = h.g;
        const row = c.SCR_chaos_eez3_objects().find(r => r[3] === 0x5E), ax = row[1], ay = row[2], x0 = ax - BACK.EEZ3;
        const {w} = common(h, 'eez3', 3328, 1024, x0, 334, viewW, viewH);
        g.chaosCollectedFlags = 63; g.player = 1;
        c.chaos_level_install_layout();
        c.chaos_eez_boss_register(row); g.chaosEezBoss.collected = 63;
        const p = h.newPlayer(x0, ay, {state: 1, move: 0, bg: 2, contacts: 2});
        g.chaosCam = c.chaos_cam_new(w.cam.x, w.cam.y, viewW);
        return {h, c, g, w, p, sample: () => {
            const b = g.chaosEezBoss, sl = ((g.chaosCarrier && g.chaosCarrier.slots) || []).filter(q => q && q.boss_actor && q.type >= 0x5E && q.type <= 0x63);
            const s = sl.find(q => q.type === 0x5E || q.type === 0x60) || sl[0];
            return {act: b.active, mode: b.mode, bs: s ? s.state : -1, bx: s ? c.chaos_eez_boss_x(s) : null, by: s ? c.chaos_eez_boss_y(s) : null, bfr: s ? s.frame : null, right: b.right, left: b.left, bot: b.bottom, enc: b.encounter};
        }};
    },
};

function stepOrder(c) {
    if (c.chaos_camera_follow_allowed()) c.chaos_camera_ordinary_step();
    c.chaos_goal_camera_step();
    c.chaos_boss_camera_step();
    c.chaos_51_camera_step();
    c.chaos_56_camera_step();
    c.chaos_54_camera_step();
    c.chaos_eez_boss_camera_step();
    c.chaos_59_camera_step();
}

function run(zone, viewW, viewH, scenario, stopX = 0) {
    const S = BUILD[zone](viewW, viewH), {h, c, w, p} = S, core = p.chaosCore;
    const cols = {};
    let lockU = null;
    for (let u = 1; u <= FRAMES; u++) {
        p.x = Math.floor(core.xu / 256); p.y = Math.floor(core.yu / 256) + 5;
        const right = !(scenario === 'stop' && lockU !== null) && !(stopX && Math.floor(core.xu / 256) >= stopX);
        h.frame({right});
        stepOrder(c);
        const s = S.sample();
        if (lockU === null && s.mode >= 2) lockU = u;
        const row = Object.assign({u, px: Math.floor(core.xu / 256), py: Math.floor(core.yu / 256), cx: w.cam.x, cy: w.cam.y, pst: core.state, vx: core.vx}, s);
        for (const [k, v] of Object.entries(row)) (cols[k] = cols[k] || []).push(typeof v === 'boolean' ? (v ? 1 : 0) : v);
    }
    return cols;
}

function build() {
    let head = null;
    try { head = cp.spawnSync('git', ['-C', POC, 'rev-parse', 'HEAD']).stdout.toString().trim() || null; } catch (e) { head = null; }
    const zones = {};
    for (const zone of Object.keys(BUILD)) {
        zones[zone] = {};
        for (const [w, hgt] of WIDTHS) {
            zones[zone]['w' + w] = {view: [w, hgt]};
            for (const sc of ['hold', 'stop']) zones[zone]['w' + w][sc] = run(zone, w, hgt, sc);
        }
    }
    // GPZ3 at 348: where Sonic stops (RIGHT released at world X) decides how far the camera has run ahead of the width-adjusted fight target 1571
    const sweep = [];
    for (const x of [1550, 1600, 1650, 1700, 1740, 1760, 1800, 1850]) {
        const cols = run('GPZ3', 348, 196, 'hold', x);
        let mx = -1, best = 0;
        for (const cx of cols.cx) { mx = Math.max(mx, cx); best = Math.max(best, mx - cx); }
        sweep.push({stop_world_x: x, max_camera_x: mx, camera_x_retreat: best, final_camera: [cols.cx[cols.cx.length - 1], cols.cy[cols.cy.length - 1]]});
    }
    return {
        gpz3_w348_stop_x_sweep: sweep,
        description: 'POC per-update boss-arrival series through the shipped functions in the node VM harness (Step_2 order). Columns are parallel arrays indexed by update. Sonic starts on the act floor BACK px left of the boss placement, RIGHT held (hold) or released at the first update the boss camera owner reports mode >= 2 (stop).',
        evidence: 'POC-SOURCE MODEL (node VM, shipped GML); not GameMaker; not Windows',
        poc_checkout_head: head, back_px: BACK, updates: FRAMES, widths: WIDTHS.map(x => x.join('x')),
        mode_semantics: {THZ3: '1 follow / 2 lock-hold / 3 pan+fight / 4 release', GPZ3: '1 takeover follow / 2 pan to fight target / 3 fight hold / 4 release',
            SEZ3: '1 follow / 2 lock-hold / 3 pan / 4 release', MGHZ3: '1 follow / 2 lock-hold / 3 pan / 4 release', AQZ3: '1 follow / 2 lock-hold / 3 pan / 4 release', EEZ3: '0 ordinary follow (limits written by the boss) / 3 pan'},
        zones,
    };
}

const text = JSON.stringify(build()) + '\n';
if (process.argv.includes('--write')) { fs.mkdirSync(path.dirname(OUT), {recursive: true}); fs.writeFileSync(OUT, text); console.log('wrote', OUT, text.length); }
else if (process.argv.includes('--check')) {
    const cur = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : null, now = JSON.parse(text);
    if (cur) { delete cur.poc_checkout_head; delete now.poc_checkout_head; }
    const same = cur !== null && JSON.stringify(cur) === JSON.stringify(now);
    console.log('CHECK poc-series', same ? 'identical (checkout head ignored)' : 'DIFFERENT'); process.exit(same ? 0 : 1);
} else process.stdout.write(text);
