// C3-BX correction CANDIDATES as exact in-memory source patches of the P4 POC GML. Research side only: the patches are applied to the text the node VM harness reads (fs.readFileSync is
// wrapped for the named files); no file of the POC checkout is ever written, and each replacement must match the P4 source EXACTLY ONCE or the run aborts.
// The patch table is also the "exact diff" printed in the report (docs/c3bx-boss-entrance-exit-audit.md).
//
//   C3BX_PATCH=A1,A2 POC=<P4 checkout> node tools/c3bx_poc_exit_run.js ...
//
//   A1  AQZ3 exit: delete the explicit widescreen clear adapter - the mode-4 branch that pins the camera to the fight view and freezes it, and the $81BD viewport-callback lock that
//       writes camera_left = camera_right = fight_x. Wide mode 4 then runs the branch that already exists for it (post-clear follow with the restored right limit and the final world cap).
//   B1  THZ3 walk-on (keep-right framing, same family as the accepted GPZ3/SEZ3/MGHZ3 width-adjusted targets): the camera is capped at 1664-(W-256) while the boss waits (mode 1, wide only), the pan
//       target and the state 18 -> 6 gate shift by (W-256). The boss world X (1936 -> 1902), its trajectory and every boss mechanic are untouched; the camera, not the boss, moves.
//   A2  Shared post-clear follow speed in WIDE views: the 4 px/update adapter cap becomes the recovered follow maximum, 7 px/update (CHAOS_54_FOLLOW_RIGHT), for the camera X in the
//       defeat-release modes of AQZ3 (chaos_59_post_clear_x), SEZ3 (chaos_54_post_clear_x), MGHZ3 (chaos_56_post_defeat_x), THZ3 (chaos_boss_follow_step mode 4) and GPZ3 (mode 4).
//       Sonic runs state $20 at 6 px/update, so a 4 px cap makes the camera fall behind and the shared freeze at EDGE(RIGHT,-7) fires before the world edge.
const fs = require('fs'), path = require('path');

const PATCHES = {
    B1: [
        {file: 'scripts/SCR_chaos_boss/SCR_chaos_boss.gml',
         old: "    if (cp_mode == 1) cp_lim.left=max(cp_lim.left,cp_b.camera_min);\n",
         new: "    if (cp_mode == 1) { cp_lim.left=max(cp_lim.left,cp_b.camera_min); if (cp_vp.w > 256) cp_lim.right=min(cp_lim.right,1664-(cp_vp.w-256)); }\n"},
        {file: 'scripts/SCR_chaos_boss/SCR_chaos_boss.gml',
         old: "        cp_x=cp_vp.left+sign(CHAOS_BOSS_CAMERA_X-cp_vp.left);\n",
         new: "        cp_x=cp_vp.left+sign((CHAOS_BOSS_CAMERA_X-(cp_vp.w-256))-cp_vp.left);\n"},
        {file: 'scripts/SCR_chaos_boss/SCR_chaos_boss.gml',
         old: "        if (chaos_boss_x(cp_b)-cp_b.camera_x <= 223) chaos_boss_set_state(cp_b,6);\n",
         new: "        if (chaos_boss_x(cp_b)-cp_b.camera_x <= 223+(cp_vp.w-256)) chaos_boss_set_state(cp_b,6);\n"},
    ],
    A1: [
        {file: 'scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml',
         old: "    } else if (cp_b.camera_mode == 4 && cp_wide) {\n        // Explicit wide clear adapter: state $20 runs off the fixed fight view.\n        cp_x=cp_b.fight_x; cp_y=cp_b.fight_y; cp_b.frozen=true;\n    } else if (cp_b.camera_mode == 4) {\n",
         new: "    } else if (cp_b.camera_mode == 4) {\n"},
        {file: 'scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml',
         old: "    if (cp_pc == $81BD && cp_b.clear && cp_vp.w > 256) {\n        cp_b.camera_left=cp_b.fight_x; cp_b.camera_right=cp_b.fight_x;\n    }\n",
         new: ""},
    ],
    A2: [
        {file: 'scripts/SCR_chaos_aqz_boss/SCR_chaos_aqz_boss.gml',
         old: "if (cp_w > 256) cp_d=clamp(chaos_59_follow_delta(cp_px-cp_x,cp_b.cam_lead),-4,4);",
         new: "if (cp_w > 256) cp_d=clamp(chaos_59_follow_delta(cp_px-cp_x,cp_b.cam_lead),-7,7);"},
        {file: 'scripts/SCR_chaos_sez_boss/SCR_chaos_sez_boss.gml',
         old: "if (cp_w > 256) cp_d=clamp(chaos_54_follow_delta(cp_px-cp_x,cp_b.cam_lead),-4,4);",
         new: "if (cp_w > 256) cp_d=clamp(chaos_54_follow_delta(cp_px-cp_x,cp_b.cam_lead),-7,7);"},
        {file: 'scripts/SCR_chaos_mghz_boss/SCR_chaos_mghz_boss.gml',
         old: "if (cp_w > 256) cp_d=clamp(chaos_56_follow_delta(cp_px-cp_x,cp_b.cam_lead),-4,4);",
         new: "if (cp_w > 256) cp_d=clamp(chaos_56_follow_delta(cp_px-cp_x,cp_b.cam_lead),-7,7);"},
        {file: 'scripts/SCR_chaos_boss/SCR_chaos_boss.gml',
         old: "if (cp_vp.w > 256) { cp_cam.x=cp_x0+clamp(cp_cam.x-cp_x0,-4,4); cp_cam.y=cp_y0+clamp(cp_cam.y-cp_y0,-4,4); }",
         new: "if (cp_vp.w > 256) { var cp_cap=(cp_mode == 4) ? 7 : 4; cp_cam.x=cp_x0+clamp(cp_cam.x-cp_x0,-cp_cap,cp_cap); cp_cam.y=cp_y0+clamp(cp_cam.y-cp_y0,-4,4); }"},
        {file: 'scripts/SCR_chaos_gpz_boss/SCR_chaos_gpz_boss.gml',
         old: "if (cp_vp.w>256) { cp_x+=clamp(cp_follow_x-cp_x,-4,4);cp_y+=clamp(cp_follow_y-cp_y,-4,4); }",
         new: "if (cp_vp.w>256) { var cp_cap=(cp_b.camera_mode==4) ? 7 : 4; cp_x+=clamp(cp_follow_x-cp_x,-cp_cap,cp_cap);cp_y+=clamp(cp_follow_y-cp_y,-4,4); }"},
    ],
};

function install(names, poc) {
    const sel = names.filter(Boolean).flatMap(n => { if (!PATCHES[n]) throw Error('unknown patch ' + n); return PATCHES[n]; });
    if (!sel.length) return;
    const real = fs.readFileSync, byFile = {};
    for (const p of sel) (byFile[path.resolve(poc, p.file)] = byFile[path.resolve(poc, p.file)] || []).push(p);
    fs.readFileSync = function (f, ...rest) {
        const out = real.call(fs, f, ...rest);
        const key = typeof f === 'string' ? path.resolve(f) : null;
        if (key && byFile[key] && typeof out === 'string') {
            let t = out;
            for (const p of byFile[key]) {
                const n = t.split(p.old).length - 1;
                if (n !== 1) throw Error(`patch target not found exactly once (${n}) in ${p.file}: ${p.old.slice(0, 70)}`);
                t = t.replace(p.old, () => p.new);
            }
            return t;
        }
        return out;
    };
}

module.exports = {PATCHES, install};
