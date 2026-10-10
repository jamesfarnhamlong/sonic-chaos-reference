// Read-only execution of shipped POC code. No input or player pinning after hit.
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'../../SonicChaos_POC_aqz_p3');
const {loadHost}=require(root+'/verification/chaos_world_harness');
const results=[];
for(const flat of [true,false])for(const x of flat?[1000]:[1743,1750,1800,1856]){
 const h=loadHost(),c=h.ctx,g=h.g,w=h.world;h.reset();w.follow=false;
 if(flat){g.chaosTileIds=Array(4096).fill(0);for(let i=0;i<128;i++)g.chaosTileIds[20*128+i]=1;w.cam={x:872,y:526,w:256,h:192};}
 else {c.room=c.ROM_chaos_aqz3;w.roomWidth=2560;w.roomHeight=512;w.cam={x:1727,y:78,w:256,h:192};c.chaos_level_install_layout();g.chaosAqz59=c.chaos_59_new();Object.assign(g.chaosAqz59,{active:true,camera_mode:3,camera_owned:true});}
 const y=flat?622:238,p=h.newPlayer(x,y,{state:1,move:0,bg:2,contacts:2,vy:1792,previous:0x82}),k=p.chaosCore;
 g.ring=1;h.frame({});
 const b=c.chaos_59_new(),shot=c.chaos_59_slot(93,0,x,y,0);shot.ex=8;shot.ey=16;shot.flags3=128;
 c.chaos_59_damage_contact(shot,k,true);
 // Shipped object-phase handoff.
 c.chaos_contact_promote(k);
 const rows=[];
 for(let u=0;u<=300&&!p.dead;u++){
  if(u===130&&!flat&&x<=1750){shot.xu=k.xu;shot.yu=k.yu;c.chaos_59_damage_contact(shot,k,true);c.chaos_contact_promote(k);}
  h.frame({});rows.push({u,x:k.xu/256,y:k.yu/256,vx:k.vx,vy:k.vy,state:k.state,next:k.next,rings:g.ring,lr:c.chaos_lr_list().map(r=>({x:c.chaos_lr_pixel_x(r),y:c.chaos_lr_pixel_y(r),vy:r.vy,age:r.age,sparkle:r.sparkle}))});
 }
 results.push({flat,x,rows});
}
fs.writeFileSync(path.resolve(__dirname,'../data/rom-cache/natural-lost-ring-poc.json'),JSON.stringify(results,null,1)+'\n');
console.log(results.map(v=>({flat:v.flat,x:v.x,entry:v.rows[0],u17:v.rows[17],landing:v.rows.find(r=>r.u>0&&r.next===5),pickup:v.rows.find(r=>r.rings===1)})));
