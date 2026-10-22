// ROM-free accepted-source audit. Usage: node tools/c2r1_audit.js <accepted-POC>
const fs=require('fs'),path=require('path'),vm=require('vm'),cp=require('child_process'),assert=require('assert'),crypto=require('crypto');
const poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c3bx1');
const out=path.resolve(__dirname,'../data/c2r1');fs.mkdirSync(out,{recursive:true});
const baseline='d1ef8fc42571fb01829d370671a96287d9ae6d93';
assert.equal(cp.execFileSync('git',['rev-parse','HEAD'],{cwd:poc,encoding:'utf8'}).trim(),baseline);
const before=cp.execFileSync('git',['status','--porcelain'],{cwd:poc,encoding:'utf8'});
const {loadHost}=require(path.join(poc,'verification/chaos_world_harness.js'));
const h=loadHost(null),c=h.ctx,rows=[];let checks=0;
const geometryPath=path.resolve(__dirname,'../data/rom-cache/collision-geometry.json');
const geometry=JSON.parse(fs.readFileSync(geometryPath,'utf8'));
const extentFor=state=>geometry.player_extents.sonic_type_1.find(r=>r.state===state).extents_x_y[0][0];
function eq(a,b){assert.deepStrictEqual(a,b);checks++;}
function record(id,width,input,actual,oracle,status){rows.push({id,width,input,actual,oracle,status});}
// Extents recovered by animation engine $6595/$659A and consumed by $6328.
// No altered GML or proposed physics is executed. Expected output comes from
// cached extent evidence plus the accepted shared overlap helper's closed box.
for(const width of [256,348]){
 h.world.cam.w=width;
 for(const state of [1,9,10,11,14,15])for(const side of [-1,1]){
  const pex=extentFor(state);
  let a=c.SCR_cc_new((100+side*20),100);a.state=a.next=state;a.move=state===15?2:0;
  const actual=c.chaos_type21_resolve(a,100,100,false);
  const expected=pex===9?2:0;
  eq(actual,0);record('C2-EXT-21',width,{state,dx:side*20,dy:0},actual,expected,actual===expected?'proven-match':'proven-gap');
  a=c.SCR_cc_new(100+side*25,84);a.state=a.next=state;a.vy=0;
  const platform={chaosVY:0,chaosOwnerId:9,chaosX:100};
  const support=c.chaos_platform28_support(platform,a,100);
  const expectedSupport=pex===9;
  eq(support,false);record('C2-EXT-28',width,{state,dx:side*25,dy:-16},support,expectedSupport,support===expectedSupport?'proven-match':'proven-gap');
  const bits=c.chaos_spike1b_contact_bits(100+side*25,76,100,100);
  const expectedBits=pex===9?1:0;
  eq(bits,0);record('C2-EXT-1B',width,{state,dx:side*25,dy:-24},bits,expectedBits,bits===expectedBits?'proven-match':'proven-gap');
 }
 // Spring launch is pure: no camera input, X speed retained, ordinary flight not attack.
 for(const strong of [false,true])for(const vx of [-1024,0,1024]){
  const a=c.SCR_cc_new(200,200);a.vx=vx;a.vy=0;a.move=2;a.bg=2;
  eq(c.chaos_spring26_launch(a,strong),true);eq(a.vx,vx);eq(a.move&3,1);eq(a.next,11);
  record('C2-SPRING-LAUNCH',width,{strong,vx},{vx:a.vx,vy:a.vy,next:a.next,move:a.move}, {vx,vy:strong?-1888:-1280,next:11,move:1},'proven-match');
 }
}
// Historical oscillation search: real THZ1 map, player+adapter in mocked host.
// This is a POC-only discovery grid, not a paired ROM replay or natural route.
const searches=[];
for(const width of [256,348])for(const state of [5,9,11,14])for(const x of [240,272,304,336,368,400]){
 const host=loadHost(null);host.world.cam.w=width;
 const p=host.newPlayer(x,780,{state,move:state===9?2:state>=11?1:0,vx:256,vy:state===11?-1888:0});
 host.g.ring=10;const trace=[];let flips=0,last=0,error=null;
 try{for(let n=0;n<96;n++){host.frame({});const a=p.chaosCore;const s=Math.sign(a.vx);if(s&&last&&s!==last)flips++;if(s)last=s;
 trace.push({n,xu:a.xu,yu:a.yu,vx:a.vx,vy:a.vy,state:a.state,next:a.next,move:a.move,bg:a.bg,contacts:a.contacts,previous:a.previous,modifier:a.modifier,support:a.support});if(p.dead)break;}}
 catch(e){error=e.message;}
 searches.push({width,state,x,y:780,flips,error,trace});
}
// Representative ordinary-act terrain windows: canonical map data is read in place.
// These are seeded contacts, not natural approach routes; camera stays mocked.
const coverage=[];
for(const act of ['thz1','gpz1','mghz1','sez1','aqz1','eez1'])for(const width of [256,348]){
 const host=loadHost(null),ctx=host.ctx;host.world.cam.w=width;
 ctx.room=ctx['ROM_chaos_'+act];ctx.chaos_level_install_layout();
 if(act==='mghz1')host.g.chaosMghzEffects=ctx.chaos_mghz_effect_new();
 if(act==='sez1')host.g.chaosSezEffects=ctx.chaos_sez_effect_new();
 for(const kind of [1,2,3,5]){
  const mw=host.g.chaosMapWidth||128;
  const index=host.g.chaosTileIds.findIndex((t,i)=>i>mw&&i%mw>2&&i%mw<mw-3&&(host.g.chaosHeaders0[t][0]&31)===kind);
  if(index<0){coverage.push({act,width,kind,status:'not-audited',reason:'No eligible sample found in this act; no placement invented'});continue;}
  const x=(index%mw)*32+16,y=Math.floor(index/mw)*32+8;
  host.reset();const p=host.newPlayer(x,y,{state:14,move:1,vy:256,previous:host.g.chaosHeaders0[host.g.chaosTileIds[index]][0]});host.g.ring=10;
  const trace=[];let error=null;
  try{for(let n=0;n<24;n++){if(act==='mghz1')host.g.chaosMghzEffects.frame++;if(act==='sez1')host.g.chaosSezEffects.frame++;host.frame({});const a=p.chaosCore;trace.push({n,xu:a.xu,yu:a.yu,vx:a.vx,vy:a.vy,state:a.state,next:a.next,bg:a.bg,contacts:a.contacts,previous:a.previous,modifier:a.modifier});if(p.dead)break;}}
  catch(e){error=e.message;}
  coverage.push({act,width,kind,index,x,y,status:'unresolved',reason:'POC-only seeded sequence; no matching cached ROM initial state',error,trace});
 }
}
const sources={};for(const n of ['SCR_chaos_core','SCR_chaos_attack','SCR_chaos_spike1b','SCR_chaos_platform','SCR_chaos_adapter','SCR_chaos_objects','SCR_chaos_spring']){
 const rel=`scripts/${n}/${n}.gml`;sources[rel]=crypto.createHash('sha256').update(fs.readFileSync(path.join(poc,rel))).digest('hex');}
for(const rel of ['verification/chaos_world_harness.js','verification/fixtures.json','verification/monitor-support-fixtures.json','POC_notes/rom-cache/spring-interaction.json','POC_notes/rom-cache/platform-spike-collision.json','POC_notes/rom-cache/player-attack-badnik.json'])sources[rel]=crypto.createHash('sha256').update(fs.readFileSync(path.join(poc,rel))).digest('hex');
sources['Research:data/rom-cache/collision-geometry.json']=crypto.createHash('sha256').update(fs.readFileSync(geometryPath)).digest('hex');
eq(cp.execFileSync('git',['status','--porcelain'],{cwd:poc,encoding:'utf8'}),before);
const result={baseline,researchParent:'637180aa3d658916b86af84b48b428ab2753f04a',evidence:'Accepted GML in node VM; cached ROM contracts, no new emulator or Windows execution',checks,sources,rows,searches,coverage};
fs.writeFileSync(path.join(out,'source-audit.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({checks,rows:rows.length,gaps:rows.filter(r=>r.status==='proven-gap').length,searches:searches.length,searchErrors:searches.filter(s=>s.error).map(s=>s.error),maxFlips:Math.max(...searches.map(s=>s.flips))}));
