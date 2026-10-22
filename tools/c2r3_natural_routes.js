const fs=require('fs'),path=require('path'),cp=require('child_process'),crypto=require('crypto'),zlib=require('zlib'),assert=require('assert');
const poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c2e1'),root=path.resolve(__dirname,'..'),out=path.join(root,'data/c2r3');fs.mkdirSync(out,{recursive:true});
assert.equal(cp.execFileSync('git',['rev-parse','HEAD'],{cwd:poc,encoding:'utf8'}).trim(),'4eb684911c5785667181b9d3f940b1dc820e66d1');const status=()=>cp.execFileSync('git',['status','--porcelain'],{cwd:poc,encoding:'utf8'});assert.equal(status(),'');
const {loadHost}=require(path.join(poc,'verification/chaos_world_harness.js'));
const roomPath='rooms/ROM_chaos_thz1/ROM_chaos_thz1.yy',room=JSON.parse(fs.readFileSync(path.join(poc,roomPath),'utf8').replace(/,\s*([}\]])/g,'$1'));
const instances=room.layers.filter(l=>l.instances).flatMap(l=>l.instances),order=new Map(room.instanceCreationOrder.map((v,i)=>[v.name,i]));
const objects=instances.filter(o=>/^OBJ_(chaos_object_(21|27|10|spring_26_normal|spring_26_span|spring_26_weak)|chaos_platform|chaos_spikes)$/.test(o.objectId?.name)).sort((a,b)=>order.get(a.name)-order.get(b.name));
const keys='xu yu vx vy state next move player_flags held pressed bg contacts support modifier previous tile input_delta surface_delta damage_request contact'.split(' '),pick=a=>Object.fromEntries(keys.map(k=>[k,a[k]]));const routes=[];
for(const width of [256,348])for(const policy of ['right','jump-at-760','release-on-ramp','lower-spring-return']){
 const h=loadHost(null),c=h.ctx,w=h.world;w.cam.w=width;w.cam.h=196;
 const start=c.chaos_act_entry(0).start,p=h.newPlayer(...start,{state:1,move:0});p.chaosCore.previous=c.SCR_cc_lookup(start[0],start[1]+18,0).flags;
 for(const o of objects){const name=o.objectId.name;if(name==='OBJ_chaos_object_27'){assert.ok(c[name]!==undefined);const b=h.newInstance(name,o.x,o.y);b.stepPath=`objects/${name}/Step_0.gml`;w.badniks.push(b);}else h.create(c[name],o.x,o.y);}
 let frame=-1,phase='frame',writes=[],jumped=false,released=false,lowerStage=0;const cc=p.chaosCore;
 for(const name of ['SCR_cc_ramp','SCR_cc_jump','SCR_cc_fall','SCR_cc_spring','SCR_chaos_type21_top_bounce','chaos_spring26_launch','SCR_cc_hurt_rom','chaos_spike1b_contact']){const orig=c[name];c[name]=function(...args){const before=pick(cc),old=phase;phase=name;try{return orig(...args);}finally{const after=pick(cc);if(JSON.stringify(before)!==JSON.stringify(after))writes.push({writer:name,before,after});phase=old;}};}
 const trace=[];let error=null,stop='budget';try{for(frame=0;frame<600;frame++){
  let input={right:true};if(policy==='jump-at-760'){if(!jumped&&cc.xu/256>=760){input={right:true,jump:true,jumpPress:true};jumped=true;}}
  if(policy==='release-on-ramp'&&(cc.modifier!==0||released)){released=true;input={};}
  if(policy==='lower-spring-return'){if(lowerStage===0&&cc.xu/256>=870)lowerStage=1;if(lowerStage===1&&cc.yu/256>=800)lowerStage=2;if(lowerStage===2&&cc.xu/256<=688)lowerStage=3;input=lowerStage===0?{right:true}:lowerStage===2?{left:true}:{};}
  writes=[];const before=pick(cc);h.frame(input);trace.push({frame,input,before,after:pick(cc),facing:c.chaos_player_draw_xscale(p),camera:{...w.cam},writers:writes,spikes:w.spikes.map(o=>({x:o.chaosX,y:o.chaosY,active:o.chaosActive,state:o.chaosState,timer:o.chaosTimer,cooldown:o.chaosCooldown})),springs:w.springs.map(o=>[o.chaosBaseX,o.chaosLayoutY,o.chaosState]),patrol:w.badniks.filter(o=>o.object_index===c.OBJ_chaos_object_21).map(o=>[o.chaosOriginX,o.x,o.y,o.chaosState,o.chaosAsleep])});
  if(p.dead||cc.next===31){stop='death';break;}if(cc.xu/256>1456){stop='bounded-region-exit';break;}
 }}catch(e){error=e.stack;stop='host-error';}
 routes.push({width,policy,start,objects:objects.map(o=>[o.objectId.name,o.x,o.y]),stop,error,trace});
}
const summary=routes.map(r=>({width:r.width,policy:r.policy,stop:r.stop,error:r.error,updates:r.trace.length,last:r.trace.at(-1)?.after,writers:[...new Set(r.trace.flatMap(t=>t.writers.map(w=>w.writer)))]}));
fs.writeFileSync(path.join(out,'natural-attempts.json.gz'),zlib.gzipSync(JSON.stringify({poc:'4eb684911c5785667181b9d3f940b1dc820e66d1',roomHash:crypto.createHash('sha256').update(fs.readFileSync(path.join(poc,roomPath))).digest('hex'),method:'Start-of-act source host, room placements unchanged; mocked camera, no full ring manager; not ROM/Windows execution',routes})+'\n',{level:9}));fs.writeFileSync(path.join(out,'natural-summary.json'),JSON.stringify(summary,null,2)+'\n');assert.equal(status(),'');console.log(JSON.stringify(summary));
