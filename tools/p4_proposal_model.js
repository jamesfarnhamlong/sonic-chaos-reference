// P4 preflight: PROPOSAL MODEL (not POC code, nothing in the POC checkout is edited).
// The shipped functions of the final V1/T1 source are executed in the node VM harness; for the four packages of the contract the model replaces ONE decision in memory, in the research
// process only, to show which camera series the contract produces:
//   T3-A  boss modes 1-2 (GPZ3, SEZ3, MGHZ3, AQZ3): the C1-I ordinary follow (chaos_cam_follow) with the boss limits instead of the zone's centre/legacy-Y rule. Wide: per-axis movement
//         bounded to 4 px from the live camera - the same rule V1/T1 already ships for THZ3 (chaos_boss_follow_step)
//   T3-B  AQZ3 trigger: left limit := camera every update in modes 1-2, right limit := camera at the trigger ($8199 + $0356)
//   T3-C  GPZ3 creation: right limit 1664 - max(0, W-256)
//   T3-E  SEZ3/MGHZ3 wide only (secondary, 400 px check): right limit <= the width-adjusted pan target from creation (the T3-C pattern); P4_EARLY_LIMIT=0 switches it off
//   T3-D  EEZ3 pan (mode 3): 1 px/update on Y with no clamp to the freshly written bottom limit
// THZ3 is run unmodified (V1/T1 already implements its mode 1/2/4 follow).
//
//   POC=<v1t1 checkout> T3_OUT=data/p4/poc-series-proposal.json T3_WIDTHS=256x192,348x196,400x225 node tools/p4_proposal_model.js [--write|--check]
const fs = require('fs'), path = require('path');
const {BUILD, run, FRAMES, WIDTHS} = require('./t3_poc_boss_run.js');
const OUT = process.env.T3_OUT ? path.resolve(process.env.T3_OUT) : path.resolve(__dirname, '..', 'data', 'p4', 'poc-series-proposal.json');

function romFollow(c, S, b, lim) {
    const w = S.w, vp = c.chaos_vp_current(), core = S.p.chaosCore;
    const cam = S.g.chaosCam; cam.x = vp.left; cam.y = vp.top;
    const x0 = cam.x, y0 = cam.y;
    c.chaos_cam_follow(cam, Math.floor(core.xu / 256), c.chaos_signed_world_y(core.yu), c.chaos_camera_facing_left(core), core.lead_target, vp.w, lim, core.camera_control);
    if (vp.w > 256) { cam.x = x0 + Math.max(-4, Math.min(4, cam.x - x0)); cam.y = y0 + Math.max(-4, Math.min(4, cam.y - y0)); }
    w.cam.x = cam.x; w.cam.y = cam.y;
}

function stepFor(zone) {
    return (c, S) => {
        const b = S.ctrl(), vp = c.chaos_vp_current();
        let skip = null;
        if (zone === 'GPZ3' && b.active && b.camera_mode === 1) {
            b.camera_right = Math.min(b.camera_right, 1664 - Math.max(0, vp.w - 256));                 // T3-C
            const lim = c.chaos_camera_ordinary_limits(vp.w); lim.left = Math.max(lim.left, 0); lim.right = Math.min(lim.right, b.camera_right);
            b.camera_owned = true; romFollow(c, S, b, lim); skip = 'chaos_51_camera_step';             // T3-A
        } else if (zone === 'SEZ3' || zone === 'MGHZ3' || zone === 'AQZ3') {
            if (b.active && b.camera_mode <= 2) {      // mode 0 = the creation update itself (the shipped step already treats 0 like 1-2)
                if (zone === 'AQZ3') {                                                                 // T3-B
                    b.camera_left = Math.max(b.camera_left, vp.left);
                    if (b.camera_mode === 2 && !b._locked) { b.camera_right = Math.min(b.camera_right, vp.left); b._locked = true; }
                }
                if (process.env.P4_EARLY_LIMIT !== '0' && b.camera_mode <= 1 && (zone === 'SEZ3' || zone === 'MGHZ3')) {   // T3-E (secondary, wide only): the same early limit as T3-C, at the width-adjusted pan target
                    const tx = zone === 'SEZ3' ? c.chaos_54_target_x(vp.w) : c.chaos_56_target_x(vp.w);
                    if (vp.w > 256) b.camera_right = Math.min(b.camera_right, tx);
                }
                const lim = c.chaos_camera_ordinary_limits(vp.w); lim.left = Math.max(lim.left, b.camera_left); lim.right = Math.min(lim.right, b.camera_right);
                b.camera_owned = true; romFollow(c, S, b, lim);                                        // T3-A
                skip = zone === 'SEZ3' ? 'chaos_54_camera_step' : zone === 'MGHZ3' ? 'chaos_56_camera_step' : 'chaos_59_camera_step';
            }
        } else if (zone === 'EEZ3' && b.active && b.mode === 3 && c.chaos_eez_boss_owns_camera() && !c.chaos_eez_boss_stopped()) {   // T3-D
            let x = vp.left, y = vp.top;
            if (x < b.pan_x) { b.right = b.pan_x; x = Math.min(x + 1, b.pan_x - 1); } else if (x > b.pan_x) { b.left = b.pan_x; x--; }
            y += Math.sign(b.pan_y - y);
            x = Math.min(x, Math.max(0, S.w.roomWidth - vp.w));
            S.w.cam.x = x; S.w.cam.y = y; c.chaos_eez_boss_cache_screen(x, y); skip = 'chaos_eez_boss_camera_step';
        }
        if (c.chaos_camera_follow_allowed()) c.chaos_camera_ordinary_step();
        c.chaos_goal_camera_step();
        for (const f of ['chaos_boss_camera_step', 'chaos_51_camera_step', 'chaos_56_camera_step', 'chaos_54_camera_step', 'chaos_eez_boss_camera_step', 'chaos_59_camera_step']) if (f !== skip) c[f]();
    };
}

function build() {
    const zones = {};
    for (const zone of Object.keys(BUILD)) {
        zones[zone] = {};
        for (const [w, h] of WIDTHS) {
            zones[zone]['w' + w] = {view: [w, h]};
            for (const sc of ['hold', 'stop']) zones[zone]['w' + w][sc] = run(zone, w, h, sc, 0, zone === 'THZ3' ? undefined : stepFor(zone));
        }
    }
    return {description: 'PROPOSAL MODEL series (final V1/T1 source + in-memory camera decisions of packages T3-A..D; THZ3 unmodified). Same columns as data/t3/poc-series.json.',
            evidence: 'PROPOSAL MODEL (node VM, shipped GML + in-memory replacement of the camera decisions named in tools/p4_proposal_model.js); not POC code', updates: FRAMES, zones};
}
const text = JSON.stringify(build()) + '\n';
if (process.argv.includes('--write')) { fs.mkdirSync(path.dirname(OUT), {recursive: true}); fs.writeFileSync(OUT, text); console.log('wrote', OUT, text.length); }
else if (process.argv.includes('--check')) { const same = fs.existsSync(OUT) && fs.readFileSync(OUT, 'utf8') === text; console.log('CHECK proposal series', same ? 'identical' : 'DIFFERENT'); process.exit(same ? 0 : 1); }
else process.stdout.write(text);
