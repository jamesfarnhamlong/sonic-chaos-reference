// Read-only execution of private Package B GML in its existing source host.
// This does not compile GameMaker or execute a GPU shader.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),pkg=path.resolve(process.argv[2]);
const {loadHost}=require(path.join(pkg,'verification/chaos_world_harness.js'));
const {ctx:c,g}=loadHost(null),v=JSON.parse(fs.readFileSync(path.join(root,'data/m2r3/evidence.json')));
let checks=0;const mismatches=[];
for(const row of v.spears.rows){
 const [act,id,char,water,plane,dx,dy,clock,sleep,flags,power,request,next]=row;
 const rec=v.inventory.acts['aqz'+(act+1)].spears.find(x=>x.placement.index===id).placement;
 const p=c.SCR_cc_new(rec.world_x+dx,rec.world_y+dy);
 Object.assign(p,{character:char,zone:4,state:5,next:5,plane,move:flags,vx:123,vy:77,rings:32,immune:power===6,invuln:120});
 g.player=char;g.powerInv=power===6;g.playerWater=water;
 const s={type:60,x:rec.world_x,y:rec.world_y,ex:3,ey:13,asleep:!!sleep};
 c.chaos_aqz_enemy_contact(s,p,true,clock);
 const actualRequest=p.stage_request;
 c.chaos_contact_promote(p);c.SCR_cc_damage_gate(p);
 if(actualRequest!==request||p.next!==next)mismatches.push({row,actualRequest,next:p.next});
 checks++;
}
assert.strictEqual(mismatches.length,0,JSON.stringify(mismatches.slice(0,3)));
const layouts={};
for(const [key,a] of Object.entries(v.inventory.acts)){
 const cells=c['SCR_chaos_'+key+'_tile_ids']();
 const hash=crypto.createHash('sha256').update(Buffer.from(cells.slice(0,a.runtime_cells))).digest('hex');
 assert.strictEqual(hash,a.layout_sha256);checks++;
 layouts[key]={sha256:hash,placements:a.spears.length,terrain_candidates:a.terrain.length};
}
// Script/callback motion pairing: native object state engine in each side,
// with identical clocks and explicit sleep controls. See original motion cache.
const motions=[];
for(const fixture of JSON.parse(fs.readFileSync(path.join(root,'data/m2r3/motion.json')))){
 const rec=fixture.placement;
 const s={type:60,state:0,requested:0,script_state:-1,pc:0,timer:0,frame:0,
  callback:0,x:rec.world_x,y:rec.world_y,xu:rec.world_x*256,yu:rec.world_y*256,
  parameter:parseInt(rec.parameter),vx:0,vy:0,ex:0,ey:0,asleep:false};
 let compared=0;
 for(const r of fixture.rows){
  s.asleep=!!r.sleep;c.chaos_aqz_enemy_script(s);c.chaos_aqz_enemy_callback(s,{},false,r.clock);
  const got=[s.state,s.requested,s.frame,s.x,s.y,s.ex,s.ey];
  assert.deepStrictEqual(got,r.expected,`placement ${rec.index} step ${r.u}`);checks++;compared++;
 }
 motions.push({act:rec.act,placement:rec.index,updates:compared});
}
const terrainMismatches=[];const hurt=c.SCR_cc_hurt_rom;const trap={};
c.SCR_cc_hurt_rom=()=>{throw trap;};
for(const f of v.terrain_controls){
 const key='aqz'+(f.act+1),[x,y,vx,vy,previous]=f.input;
 c['SCR_chaos_'+key+'_profiles']();g.chaosTileIds=c['SCR_chaos_'+key+'_tile_ids']();
 g.chaosMapWidth=v.inventory.acts[key].width;g.chaosBeyondMapOpen=false;
 const p=c.SCR_cc_new(x,y);Object.assign(p,{character:f.character,state:10,next:10,zone:4,plane:f.plane,move:1,vx,vy,previous});
 let hit=false;
 try{c.SCR_cc_floor(p);c.SCR_cc_sides(p);c.SCR_cc_ceiling(p);}catch(e){if(e!==trap)throw e;hit=true;}
 const got={hit,x:Math.floor(p.xu/256),y:Math.floor(p.yu/256)};
 const expected={hit:f.output.hit,x:f.output.x,y:f.output.y};
 if(JSON.stringify(got)!==JSON.stringify(expected))terrainMismatches.push({fixture:f,actual:got});checks++;
}
c.SCR_cc_hurt_rom=hurt;
const out={method:'private Package B shipped GML source host, no native Windows/GPU',
 checks,contact_controls:v.spears.rows.length,contact_mismatches:mismatches.length,layouts,motions,
 terrain_controls:v.terrain_controls.length,terrain_mismatches:terrainMismatches};
fs.writeFileSync(path.join(root,'data/m2r3/package-controls.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify(out));
