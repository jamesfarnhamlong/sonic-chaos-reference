// T2: READ-ONLY execution of the accepted POC C1-I source (shipped GML in the POC's own node VM harness) for the two camera/player-boundary
// scenarios the Windows report describes. Evidence class: POC-SOURCE MODEL. This is not GameMaker and not Windows; it proves what the shipped
// functions compute when driven in the documented order, nothing more.
//
//   POC=<path to SonicChaos_POC at 69527335> node tools/t2_poc_model.js [--write]
//
// Frame order used (OBJ_chaos_zone Step_2): player adapter step/end + objects phase (host.frame), then chaos_camera_ordinary_step() when
// chaos_camera_follow_allowed(), then chaos_boss_camera_step(). The POC tree is never modified.
const fs = require('fs'), path = require('path');
const POC = process.env.POC || 'E:/AI/Codex/Sonic Chaos/SonicChaos_POC_c1i';
const {loadHost} = require(path.join(POC, 'verification/chaos_world_harness.js'));
const OUT = path.resolve(__dirname, '..', 'data', 't2', 'poc-model.json');

function thz3(viewW, frames, dir) {
    const host = loadHost(null), h = host.ctx, g = host.g, w = host.world;
    h.room = host.ids.ROM_chaos_thz3; h.__view_get = () => 192;
    const x0 = 1560;
    w.roomWidth = 2560; w.roomHeight = 512; w.cam = {x: x0 - 104, y: 80, w: viewW, h: 192}; w.follow = false;
    h.chaos_level_install_layout();
    g.chaosPan = h.chaos_goal_pan_new(); g.chaosCamLeft = 0;
    const p = host.newPlayer(x0, 238, {state: 1, move: 0, bg: 2, contacts: 2});
    const c = p.chaosCore;
    const boss = host.create(host.ids.OBJ_chaos_object_50, 1936, 238);
    g.chaosCam = h.chaos_cam_new(w.cam.x, w.cam.y, viewW);
    const rows = [];
    for (let u = 1; u <= frames; u++) {
        host.frame({right: dir === 'right', left: dir === 'left'});
        if (h.chaos_camera_follow_allowed()) h.chaos_camera_ordinary_step();
        h.chaos_boss_camera_step();
        const b = boss.chaosBoss, px = Math.floor(c.xu / 256), cx = w.cam.x;
        rows.push({u, px, psx: px - cx, cx, bs: b.state, mode: b.camera_mode, bx: Math.floor(b.xu / 256), bsx: Math.floor(b.xu / 256) - cx, pst: c.state});
    }
    const first = f => rows.find(f);
    const created = first(r => r.bs !== -1), lock = first(r => r.mode === 2), pan = first(r => r.mode === 3);
    const vis = first(r => r.bs !== -1 && r.bsx < viewW);
    const lockedRows = rows.filter(r => r.mode >= 2);
    const steps = rows.slice(1).map((r, i) => Math.abs(r.cx - rows[i].cx));
    const pick = r => r && {u: r.u, player_x: r.px, player_screen_x: r.psx, boss_x: r.bx, boss_screen_x: r.bsx, camera_x: r.cx, boss_state: r.bs, camera_mode: r.mode};
    return {
        view_width: viewW, updates: frames, input: dir + ' held',
        boss_created: pick(created), boss_first_anchor_inside_view: pick(vis), arena_lock_mode2: pick(lock), pan_mode3: pick(pan),
        player_screen_x_max_before_lock: Math.max(...rows.filter(r => r.mode < 2).map(r => r.psx)),
        player_screen_x_max_after_lock: Math.max(...lockedRows.map(r => r.psx)),
        player_world_x_max_after_lock: Math.max(...lockedRows.map(r => r.px)),
        first_update_player_right_of_boss_spawn_x: (first(r => r.mode >= 2 && r.px > 1936) || {}).u ?? null,
        first_update_player_beyond_view_right: (first(r => r.mode >= 2 && r.psx >= viewW) || {}).u ?? null,
        updates_player_beyond_view_right: lockedRows.filter(r => r.psx >= viewW).length,
        updates_player_right_of_boss_anchor: lockedRows.filter(r => r.px > r.bx).length,
        camera_step_at_first_mode1_update: (m1 => Math.abs(m1.cx - rows[m1.u - 2].cx))(first(r => r.mode === 1)), player_screen_x_change_at_first_mode1_update: (m1 => m1.psx - rows[m1.u - 2].psx)(first(r => r.mode === 1)),
        camera_step_max: Math.max(...steps), camera_step_max_update: steps.indexOf(Math.max(...steps)) + 2,
        final: pick(rows[rows.length - 1]),
        screen_x_samples: rows.filter(r => r.u % 20 === 0).map(r => [r.u, r.psx, r.bsx, r.cx, r.mode]),
    };
}

function signWait(viewW) {
    // THZ1 sign (3960,558), pre-contact: Sonic runs RIGHT from 3770 to 150 px before the sign, then LEFT for 320 updates. The sign is never touched.
    const host = loadHost(null), h = host.ctx, g = host.g, w = host.world;
    h.room = host.ids.ROM_chaos_thz1; h.__view_get = () => 192;
    const x0 = 3770, SX = 3960, SY = 558;
    w.roomWidth = 4096; w.roomHeight = 1024; w.cam = {x: x0 - 104, y: 430, w: viewW, h: 192}; w.follow = false;
    g.chaosPan = h.chaos_goal_pan_new(); g.chaosCamLeft = 0; g.chaosGoalContact = false;
    const p = host.newPlayer(x0, SY, {state: 1, move: 0, bg: 2, contacts: 2});
    const c = p.chaosCore;
    const sign = host.create(host.ids.OBJ_chaos_object_18, SX, SY);
    h.chaos_camera_ordinary_begin();                                   // seeds the follow state and the dynamic left limit
    w.cam.x = x0 - (viewW === 256 ? 104 : 150); g.chaosCam = h.chaos_cam_new(w.cam.x, w.cam.y, viewW);   // start record of the scenario (CENTER-relative lead at wide)
    const rows = [];
    let phase = 'right', turn = null;
    for (let u = 1; u <= 900; u++) {
        host.frame({right: phase === 'right', left: phase === 'left'});
        if (h.chaos_camera_follow_allowed()) h.chaos_camera_ordinary_step();
        const px = Math.floor(c.xu / 256), cx = w.cam.x;
        rows.push({u, phase, px, psx: px - cx, cx, left_limit: g.chaosCamLeft, contact: !!g.chaosGoalContact, state: sign.chaosSign.state});
        if (phase === 'right' && px >= SX - 150) { phase = 'left'; turn = rows[rows.length - 1]; }
        if (phase === 'left' && u - turn.u >= 320) break;
    }
    const back = rows.filter(r => r.phase === 'left');
    const raised = rows.find(r => r.left_limit > 0);
    return {
        view_width: viewW, sign_anchor: [SX, SY], contact_during_trace: rows.some(r => r.contact || r.state !== 3),
        left_limit_first_raised: raised && {u: raised.u, camera_x: raised.cx, player_x: raised.px, sign_screen_x: SX - raised.cx},
        turn_around: turn && {u: turn.u, player_x: turn.px, player_screen_x: turn.psx, camera_x: turn.cx, left_limit: turn.left_limit},
        player_screen_x_min_walking_back: Math.min(...back.map(r => r.psx)),
        player_screen_x_max_walking_back: Math.max(...back.map(r => r.psx)),
        player_world_x_min_walking_back: Math.min(...back.map(r => r.px)),
        camera_x_min_walking_back: Math.min(...back.map(r => r.cx)),
        updates_with_player_left_of_view: back.filter(r => r.psx < 0).length,
        updates_with_player_left_of_clamp16: back.filter(r => r.psx < 16).length,
        final: rows[rows.length - 1],
    };
}

const out = {
    description: 'POC C1-I (69527335) THZ3 boss arrival through the shipped functions in the node VM harness: Sonic starts at x=1560 on the flat floor (ROM clamp edges would be camera+16 / camera+247), RIGHT held. No boss state is forced. Wide views reuse the same input.',
    evidence: 'POC-SOURCE MODEL (node VM, shipped GML); not GameMaker; not Windows',
    poc_commit: '69527335011bacf22ff16bd25d3a94874a1fa563',
    thz3: [256, 348].map(w => thz3(w, 330, 'right')),
    sign_wait: [256, 348].map(w => signWait(w)),
};
const text = JSON.stringify(out, null, 1) + '\n';
if (process.argv.includes('--write')) { fs.mkdirSync(path.dirname(OUT), {recursive: true}); fs.writeFileSync(OUT, text); console.log('wrote', OUT, text.length); }
else if (process.argv.includes('--check')) { const same = fs.existsSync(OUT) && fs.readFileSync(OUT, 'utf8') === text; console.log('CHECK poc-model', same ? 'identical' : 'DIFFERENT'); process.exit(same ? 0 : 1); }
else process.stdout.write(text);
