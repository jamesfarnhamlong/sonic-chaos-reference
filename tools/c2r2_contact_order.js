const fs=require('fs'),path=require('path'),cp=require('child_process'),assert=require('assert'),crypto=require('crypto');
const poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c2e1'),out=path.resolve(__dirname,'../data/c2r2');fs.mkdirSync(out,{recursive:true});
const baseline='4eb684911c5785667181b9d3f940b1dc820e66d1';assert.equal(cp.execFileSync('git',['rev-parse','HEAD'],{cwd:poc,encoding:'utf8'}).trim(),baseline);
const status=()=>cp.execFileSync('git',['status','--porcelain'],{cwd:poc,encoding:'utf8'});assert.equal(status(),'');
const {loadHost}=require(path.join(poc,'verification/chaos_world_harness.js'));
const keys='state next xu yu vx vy held pressed player_flags move bg contacts objects support previous tile modifier surface_delta input_delta stage_contact stage_nib stage_request contact contact_nib damage_request box_contacts box_ready'.split(' ');
const snap=a=>Object.fromEntries(keys.map(k=>[k,a[k]]));const rows=[];
// Exact THZ1 records, not a claim that these seeded approaches are naturally reached.
const scenarios=[{id:'mapped-spring',x:688,y:846,spring:[688,864]}, {id:'mapped-patrol',x:1248,y:836,badnik:[1248,862]}, {id:'combined-overlay',x:688,y:846,badnik:[688,862],spring:[688,864]}, {id:'empty-control',x:688,y:400,empty:true}];
for(const width of [256,348])for(const s of scenarios)for(const control of ['none','right','left','alternating'])for(const vx of [-256,0,256]){
 const h=loadHost(null),c=h.ctx;h.world.cam.w=width;h.g.ring=10;
 if(s.empty)h.isolate();
 const p=h.newPlayer(s.x,s.y,{state:14,move:1,vy:256,vx});
 let frame=-1,phase='setup',writes=[];const raw=p.chaosCore;
 p.chaosCore=new Proxy(raw,{set(t,k,v){if(keys.includes(k)&&t[k]!==v)writes.push({frame,writer:phase,key:k,from:t[k],to:v});t[k]=v;return true;}});
 for(const name of ['SCR_cc_input','SCR_cc_x','SCR_cc_y','SCR_cc_floor','SCR_cc_ramp','SCR_cc_spring','SCR_cc_fall','SCR_cc_walk','SCR_cc_damage_gate','SCR_cc_hurt_rom','SCR_chaos_type21_top_bounce','chaos_type21_resolve','chaos_contact_stage','chaos_request_stage','chaos_contact_promote','chaos_spring26_launch','SCR_chaos_object_spring_step','chaos_platform28_step','SCR_chaos_core_publish']){
  const orig=c[name];if(!orig)continue;c[name]=function(...args){const prev=phase;phase=name;try{return orig(...args);}finally{phase=prev;}};
 }
 if(s.spring)h.create(c.OBJ_chaos_object_spring_26_normal,...s.spring);
 if(s.badnik)h.create(c.OBJ_chaos_object_21,...s.badnik);
 const trace=[];let error=null;
 try{for(frame=0;frame<160;frame++){
 const input=control==='none'?{}:control==='alternating'?(frame%2?{left:true}:{right:true}):{[control]:true};writes=[];phase='host.frame';const before=snap(raw);h.frame(input);
 trace.push({frame,input,before,after:snap(raw),published:{x:p.x,y:p.y,facing:p.image_xscale,drawFacing:c.chaos_player_draw_xscale(p),frame:p.chaosCore.visual_anim?.frame,screenX:p.x-h.world.cam.x,cameraX:h.world.cam.x},spring:h.world.springs.map(o=>({x:o.chaosBaseX,y:o.chaosLayoutY,state:o.chaosState,timer:o.chaosTimer})),badnik:h.world.badniks.map(o=>({x:o.x,y:o.y,state:o.chaosState,vx:o.chaosVX,active:o.chaosActive,asleep:o.chaosAsleep,destroyed:!!o.destroyed})),supportReference:typeof p.chaosSupport==='object'?'instance':p.chaosSupport,writes});if(p.dead)break;
 }}catch(e){error=e.stack;}
 function flips(vals){let last=0,n=0;for(const v of vals){const sign=Math.sign(v);if(sign&&last&&sign!==last)n++;if(sign)last=sign;}return n;}
 rows.push({id:s.id,width,control,vx,placement:s,placementClass:s.id==='combined-overlay'?'synthetic translated Badnik; NOT canonical placement':'canonical THZ1 records or labelled empty control; seeded player approach',error,velocityFlips:flips(trace.map(t=>t.after.vx)),worldFlips:flips(trace.map(t=>t.after.xu-t.before.xu)),facingFlips:flips(trace.map(t=>t.published.facing)),launches:trace.flatMap(t=>t.writes).filter(w=>w.writer==='chaos_spring26_launch'&&w.key==='vy').length,stomps:trace.flatMap(t=>t.writes).filter(w=>w.writer==='SCR_chaos_type21_top_bounce'&&w.key==='vy').length,trace});
}
assert.equal(status(),'');const hashes={};for(const rel of cp.execFileSync('git',['ls-files','scripts','objects/OBJ_chaos_object_21','verification/chaos_world_harness.js'],{cwd:poc,encoding:'utf8'}).trim().split(/\r?\n/)){if(rel.endsWith('.gml')||rel.endsWith('.js'))hashes[rel]=crypto.createHash('sha256').update(fs.readFileSync(path.join(poc,rel))).digest('hex');}
const summary={scenarios:rows.length,errors:rows.filter(r=>r.error).length,launchSequences:rows.filter(r=>r.launches).length,stompSequences:rows.filter(r=>r.stomps).length,maxUnforcedWorldFlips:Math.max(...rows.filter(r=>r.control!=='alternating').map(r=>r.worldFlips)),maxUnforcedVelocityFlips:Math.max(...rows.filter(r=>r.control!=='alternating').map(r=>r.velocityFlips))};
fs.writeFileSync(path.join(out,'traces.json.gz'),require('zlib').gzipSync(JSON.stringify({baseline,researchParent:'1e34a2a666a83e107942678fe0c0497fffb3ff05',evidence:'Shipped GML in mocked Node host; no ROM or Windows execution',summary,hashes,rows})+'\n',{level:9}));
fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify({baseline,summary,rows:rows.map(({trace,...r})=>r)},null,2)+'\n');console.log(JSON.stringify(summary));assert.equal(summary.errors,0);


