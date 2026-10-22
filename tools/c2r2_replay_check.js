const fs=require('fs'),path=require('path'),zlib=require('zlib'),assert=require('assert');
const poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c2e1'),d=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.resolve(__dirname,'../data/c2r2/traces.json.gz'))));const {loadHost}=require(path.join(poc,'verification/chaos_world_harness.js'));let checks=0;
for(const row of d.rows){const h=loadHost(null),c=h.ctx,s=row.placement;h.world.cam.w=row.width;h.g.ring=10;if(s.empty)h.isolate();const p=h.newPlayer(s.x,s.y,{state:14,move:1,vy:256,vx:row.vx});if(s.spring)h.create(c.OBJ_chaos_object_spring_26_normal,...s.spring);if(s.badnik)h.create(c.OBJ_chaos_object_21,...s.badnik);
for(const t of row.trace){h.frame(t.input);for(const [key,value] of Object.entries(t.after)){assert.deepStrictEqual(p.chaosCore[key],value,`${row.id}/${row.width}/${row.control}/${row.vx}/${t.frame}/${key}`);checks++;}assert.equal(c.chaos_player_draw_xscale(p),t.published.drawFacing);checks++;}}
const result={uninstrumentedReplayChecks:checks,sequences:d.rows.length};fs.writeFileSync(path.resolve(__dirname,'../data/c2r2/replay-check.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));

