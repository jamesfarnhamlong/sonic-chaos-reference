const fs=require('fs'),path=require('path'),assert=require('assert'),zlib=require('zlib');
const poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c2e1');const {loadHost}=require(path.join(poc,'verification/chaos_world_harness.js'));const h=loadHost(null),c=h.ctx;
const table=fs.readFileSync(path.resolve(__dirname,'../data/movement-tables.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(l=>l.split(','));let checks=0;const eq=(a,b)=>{assert.deepStrictEqual(a,b);checks++;};const cases=[];
// Reduced semantic oracle from recovered $4223->$4196, $41A9 and $402A;
// numeric pairs independently read from Research CSV, not the GML tables.
for(const state of [11,14])for(const initial of [-256,-128,-32,-16,-1,0,1,16,32,128,256]){
 const a=c.SCR_cc_new(100,400);a.state=a.next=state;a.vx=initial;const pair=table.find(r=>r[0]==='no_direction'&&parseInt(r[1],16)===state).slice(3).map(Number);let v=initial,x=25600;const trace=[];
 for(let n=0;n<32;n++){const delta=v===0?0:pair[v<0?0:1]*(Math.abs(v)+128<256?2:1);v+=delta;x+=v;c.SCR_cc_input(a);c.SCR_cc_x(a);eq([a.vx,a.xu],[v,x]);trace.push({n,v,x});}cases.push({state,initial,trace});
}
// Real staged ordinary-enemy callback -> promotion -> real damage gate. No natural placement claim.
const contact=[];for(const move of [1,3])for(const side of ['above','below','left','right']){
 const a=c.SCR_cc_new(side==='left'?85:side==='right'?115:100,side==='above'?90:side==='below'?120:100);a.state=a.next=11;a.move=move;a.rings=10;
 const before={vx:a.vx,vy:a.vy,next:a.next};const result=c.chaos_type27_resolve(a,100,100,false);eq(a.contact,0);eq(a.stage_contact,1);const staged={contact:a.contact,stage:a.stage_contact,nib:a.stage_nib};c.chaos_contact_promote(a);eq(a.stage_contact,0);eq(a.contact,1);const promoted={contact:a.contact,nib:a.contact_nib};c.SCR_cc_damage_gate(a);eq(a.contact,0);if(move===1)eq(a.next,30);else eq(a.vy,side==='above'?-768:side==='below'?128:0);contact.push({move,side,before,result,staged,promoted,after:{vx:a.vx,vy:a.vy,next:a.next,move:a.move}});
}
// Zero speed preserves retained surface delta, per $4223 RET Z. It need not be zero.
for(const retained of [-24,0,24]){const a=c.SCR_cc_new(100,400);a.state=11;a.surface_delta=retained;c.SCR_cc_input(a);eq(a.surface_delta,retained);c.SCR_cc_x(a);eq(a.vx,retained);}
fs.writeFileSync(path.resolve(__dirname,'../data/c2r2/canonical-controls.json'),JSON.stringify({method:'Reduced recovered-assembly semantic model + cached CSV; not Z80 or ROM execution',checks,cases,contact},null,2)+'\n');console.log(JSON.stringify({checks,cases:cases.length,stagedContacts:contact.length}));

