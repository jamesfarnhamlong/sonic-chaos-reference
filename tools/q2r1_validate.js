// Focused evidence checks and independent, uninstrumented replay of the decisive slice.
const fs=require('fs'),path=require('path'),zlib=require('zlib'),assert=require('assert');
const root=path.resolve(__dirname,'..'),poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c2e1');
const dash=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,'data/q2r1/dash-traces.json.gz')))),ss=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,'data/q2r1/ss3-traces.json.gz'))));
assert.equal(dash.rows.length,24);assert.equal(dash.rows.filter(r=>r.status==='proven-gap').length,8);
for(const r of dash.rows){assert.equal(r.status==='proven-gap',r.water&&Math.sign(r.initial)!==r.intent);assert.equal(r.trace[0].after.modifier,0);assert.equal(r.trace[0].after.surface_delta,0);}
const {loadHost}=require(path.join(poc,'verification/chaos_world_harness.js'));
for(const r of dash.rows){const h=loadHost(),c=h.ctx,g=h.g;c.room=c['ROM_chaos_'+r.room];c.chaos_level_install_layout();if(r.water)g.chaosAqzEnv.line=r.act===1?568:788;h.world.cam.w=r.width;h.world.cam.h=196;const p=h.newPlayer(...r.seed,{state:5,move:0,bg:2,previous:129,vx:r.initial});p.image_xscale=Math.sign(r.initial);p.chaosCore.player_flags=r.initial<0?16:0;for(const t of r.trace){h.frame(t.input);for(const k of ['state','next','xu','yu','vx','vy','player_flags'])assert.equal(p.chaosCore[k],t.after[k],`${r.room}/${r.width}/${t.n}/${k}`);}}
assert.equal(ss.placements.length,7);assert.equal(ss.corners.length,28);assert.equal(ss.natural.length,2);
for(const r of ss.natural){assert.equal(r.updates,2090);assert.equal(r.collected,true);assert.equal(r.failure,null);assert.deepEqual(r.broken,[[240,622],[912,622],[1584,622],[2256,622],[2928,622]]);}
const broken=ss.corners.filter(r=>r.trace.some(t=>t.monitor.consumed));assert.equal(broken.length,12);assert.ok(broken.every(r=>r.attack));
assert.equal(JSON.parse(fs.readFileSync(path.join(root,'data/q2r1/gate/results.json')))[0].status,0);
const reg=JSON.parse(fs.readFileSync(path.join(root,'data/q2r1/register.json')));assert.equal(reg.findings.filter(r=>r.status==='proven-gap').length,1);assert.equal(reg.proposals.length,1);assert.equal(reg.new_rom_execution,false);assert.equal(reg.new_windows_execution,false);
assert.equal(new Set(reg.findings.map(r=>r.id)).size,reg.findings.length);assert.equal(reg.findings.find(r=>r.id==='Q2R1-SS3-MONITOR').status,'unresolved');
console.log('Q2-R1 PASS: 24 uninstrumented dash replays; 8 wet discrepancies/16 controls; 2 cached-input SS3 completions; 28 mapped corner fixtures; cached monitor oracle gate.');
