// Bounded replay of inherited canonical contracts, no ROM access or POC writes.
const fs=require('fs'),path=require('path'),assert=require('assert'),cp=require('child_process');
const poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c2e1'),root=path.resolve(__dirname,'..'),out=path.join(root,'data/c2r3');fs.mkdirSync(out,{recursive:true});assert.equal(cp.execFileSync('git',['rev-parse','HEAD'],{cwd:poc,encoding:'utf8'}).trim(),'4eb684911c5785667181b9d3f940b1dc820e66d1');const clean=()=>cp.execFileSync('git',['status','--porcelain'],{cwd:poc,encoding:'utf8'});assert.equal(clean(),'');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,'data/rom-cache',p),'utf8'));
const {loadHost}=require(path.join(poc,'verification/chaos_world_harness.js'));let checks=0;const eq=(a,b,label)=>{assert.deepStrictEqual(JSON.parse(JSON.stringify(a)),JSON.parse(JSON.stringify(b)),label);checks++;};const result={method:'Cached original contracts/observations vs shipped GML in Node VM; controlled samples, not new ROM/Windows execution',widths:[256,348],sez:[],aqz:[],mghz:[],eez:[]};
const SEZ=read('sez/surface-runtime-contracts.json'),WATER=read('aqz/water-runtime.json'),MGHZ=read('mghz/surface-1b-ceiling-spikes.json');
for(const width of [256,348]){
 // SEZ original-frame cached drop: known fixture metadata says120 but inherited verifier proved154 from row9. Reuse154 explicitly.
 const h=loadHost(null),c=h.ctx,g=h.g;h.world.cam.w=width;h.world.cam.h=196;c.room=c.ROM_chaos_sez1;c.chaos_level_install_layout();g.chaosSezEffects=c.chaos_sez_effect_new();g.chaosSezBossActive=false;
 const p=h.newPlayer(2160,154,{state:14,move:129});p.chaosCore.invuln=1e9;const cached=SEZ.oracle_vectors.trace_vectors.find(t=>t.id==='crumble_drop_sez1_67_6'),trace=[];
 for(let u=1;u<=45;u++){h.frame({});c.chaos_sez_effect_step(g.chaosSezEffects,false,0);const a=p.chaosCore,row=[u,Math.floor(a.xu/256),Math.floor(a.yu/256),a.vx,a.vy,a.state,a.next,a.bg&2,a.move];const expected=cached.rows.find(r=>r[0]===u);if(expected)eq(row,expected.slice(0,9),'SEZ cached drop '+u);trace.push({u,row,support:a.support,cell:g.chaosTileIds[6*128+67],spawns:g.chaosS2.spawns.length,breaks:g.chaosS2.replaced.length});}
 const controls=[];for(const vector of SEZ.oracle_vectors.table_vectors.crumble_rider_a344.filter(r=>[5,14].includes(r.input.player_state_d501)&&[0,1].includes(r.input.movement_d503))){const a=c.SCR_cc_new(100,400);a.state=vector.input.player_state_d501;a.move=vector.input.movement_d503;a.vy=256;const yes=c.chaos_s2_rider_hold({y:216},a);eq(yes,vector.expect.hold_applied,'hold gate');eq([a.yu/256,a.vy],yes?[176,0]:[400,256],'hold values');controls.push({vector,actual:{hold:yes,y:a.yu/256,vy:a.vy}});}
 result.sez.push({width,case:'cached drop at unchanged SEZ1 cell67,6, fixture start154 (metadata120 unresolved)',trace,controls,spawns:g.chaosS2.spawns,replaced:g.chaosS2.replaced});
 // AQZ entry threshold, signed high-byte gate, rising/no-attack/prior-wet controls from cached original vectors.
 for(const dy of [-1,0])for(const vx of [-1023,1023,1024])for(const attack of [0,2]){
  const vector=WATER.crossing_vectors.find(r=>r.dy===dy&&r.vx===vx&&r.vy===0&&r.attack===attack&&r.prior_water===0);assert.ok(vector);
  const e=c.chaos_aqz_env_new(1),pool=c.chaos_s2_new(),a=c.SCR_cc_new(100,568+dy);e.line=568;Object.assign(a,{vx,vy:0,move:1|attack,water:0});c.chaos_aqz_cross(e,a,pool);const actual={water:a.water,vy:a.vy,splash:e.spawns.some(r=>r[1]===14)};eq(actual,{water:vector.water,vy:vector.result_vy,splash:vector.splash},'AQZ crossing');result.aqz.push({width,vector,actual});
 }
 // MGHZ real row11 run, no map edits. Equality boundaries and owner/rising immunity controls.
 c.room=c.ROM_chaos_mghz2;c.chaos_level_install_layout();
 const rect=MGHZ.ceiling_spikes.real_runs_check.results['mghz2:0x3F@cells[27, 43, 11]'].expected[0];
 for(const [y,vy,owner,inv,state] of [[357,-1,0,0,10],[358,-1,0,0,10],[382,-1,0,0,10],[383,-1,0,0,10],[358,0,0,0,10],[358,256,9,0,10],[358,-1,0,128,10],[358,-1,0,0,30]]){
  const a=c.SCR_cc_new(864,y);Object.assign(a,{zone:3,state,next:state,vy,support:owner,move:inv,rings:5,immune:true});const probe=c.SCR_cc_lookup(864,y-6,0);c.SCR_cc_ceiling(a);const hit=y>=rect[2]&&y<=rect[3]&&(owner!==0||vy<0)&&!inv&&state!==30;eq(a.hurt_pending,hit,'MGHZ head gate');if(hit)eq([a.next,a.vx,a.vy],[30,-256,256],'MGHZ ceiling hurt');result.mghz.push({width,input:{x:864,y,vy,owner,inv,state},block:probe.tile,canonicalRect:rect,actual:{hurt:a.hurt_pending,next:a.next,vx:a.vx,vy:a.vy,y:a.yu/256}});
 }
 // EEZ cached controlled attach/detach vectors. Oracle is inherited original-routine export, not derived from current GML.
 const O=JSON.parse(fs.readFileSync(path.join(poc,'verification/eez-p2/routine-oracle.json'),'utf8'));
 c.room=c.ROM_chaos_eez1;c.chaos_level_install_layout();
 for(const pad of [0,16])for(const frac of [0,77])for(const water of [0,1]){
  const row=O.attached.find(r=>{const i=r[0];return i[0]===pad&&i[1]===frac&&i[2]===23&&i[3]===0&&i[4]===100&&i[5]===water&&i[6]===255;});assert.ok(row);const [input,po,ao]=row;
  const a=c.SCR_cc_new(0,0),s=Object.assign(c.chaos_carrier_empty(),{type:23,state:2,requested:2,xu:1000*256,yu:100*256,vx:321,vy:123,flags4:128,parameter:2,ex:12,ey:16});g.chaosCarrier=c.chaos_carrier_new();g.chaosCarrier.slots[0]=s;
  Object.assign(a,{state:23,next:23,zone:5,xu:frac,yu:255-frac,carrier_owner:1,pressed:pad,damage_request:0,carrier_screen_y:100,water,tile:255,bg:2,rings:12,invuln:37});c.chaos_carrier_player(a);
  const actual=[a.xu,a.yu,a.vx&65535,a.vy&65535,a.next,a.move,a.player_flags,a.bg,a.invuln,Math.floor(a.rings/10)*16+a.rings%10,a.carrier_owner!==0],actor=[s.requested,s.vx&65535,s.vy&65535,s.flags3,s.flags4,s.cooldown,s.token,s.parameter,s.bg];eq(actual,po,'EEZ player');eq(actor,ao,'EEZ owner');result.eez.push({width,input,expectedPlayer:po,expectedActor:ao,actual,actor});
 }
}
result.checks=checks;assert.equal(clean(),'');fs.writeFileSync(path.join(out,'special-cases.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({checks,sez:result.sez.length,aqz:result.aqz.length,mghz:result.mghz.length,eez:result.eez.length}));
