// S0 preflight: how the POC player behaves in the first updates of the act-1 starts (shipped adapter + terrain in the node VM harness; POC read only).
//   POC=<checkout> node tools/s0_start_fall.js [--write]
// Start = chaos_acts() ROM anchor, SCR_cc_new defaults (state 1, no floor flags), no input - what OBJ_chaos_zone Create seeds. Camera = chaos_acts() camera record.
const fs = require('fs'), path = require('path');
const POC = process.env.POC;
const {loadHost} = require(path.join(POC, 'verification/chaos_world_harness.js'));
const START = {THZ1: ['thz1', [142, 654], [38, 530], 4096, 1024], GPZ1: ['gpz1', [110, 384], [0, 272], 2560, 512], MGHZ1: ['mghz1', [78, 192], [0, 80], 3840, 768]};
const out = {};
for (const [k, [room, st, cam, rw, rh]] of Object.entries(START)) {
    const h = loadHost(), c = h.ctx, g = h.g, w = h.world;
    c.room = c['ROM_chaos_' + room]; c.__view_get = () => 192; w.roomWidth = rw; w.roomHeight = rh; w.follow = false; w.cam = {x: cam[0], y: cam[1], w: 256, h: 192};
    g.chaosMghzEffects = c.chaos_mghz_effect_new(); g.chaosM3 = c.chaos_m3_new(); g.chaosSezEffects = c.chaos_sez_effect_new();
    c.chaos_level_install_layout(); g.chaosPan = c.chaos_goal_pan_new(); g.chaosCamLeft = 0; g.chaosGoalContact = false;
    const p = h.newPlayer(st[0], st[1], {state: 1, move: 0, bg: 0, contacts: 0}); const core = p.chaosCore;
    g.chaosCam = c.chaos_cam_new(w.cam.x, w.cam.y, 256);
    const rows = [];
    for (let u = 1; u <= 60; u++) {
        p.x = Math.floor(core.xu / 256); p.y = Math.floor(core.yu / 256) + 5;
        h.frame({}); if (c.chaos_camera_follow_allowed()) c.chaos_camera_ordinary_step();
        rows.push([u, Math.floor(core.yu / 256), core.state, core.contacts & 2 ? 1 : 0, w.cam.y]);
    }
    const land = rows.find(r => r[3] === 1);
    out[k] = {start: st, camera_record: cam, first_floor_contact_update: land && land[0], y_first: rows[0][1], y_at_landing: land && land[1], drop_px: land && land[1] - st[1],
              y_series_first_12: rows.slice(0, 12).map(r => r[1]), states_first_12: rows.slice(0, 12).map(r => r[2]), camera_y_first_12: rows.slice(0, 12).map(r => r[4])};
}
const t = JSON.stringify(out, null, 1) + '\n';
if (process.argv.includes('--write')) { fs.writeFileSync(path.resolve(__dirname, '..', 'data', 'p4', 's0-poc-start-fall.json'), t); console.log('wrote s0-poc-start-fall.json'); } else process.stdout.write(t);
