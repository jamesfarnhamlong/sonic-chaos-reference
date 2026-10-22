const fs=require('fs'),path=require('path'),assert=require('assert'),cp=require('child_process');const poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c2e1'),root=path.resolve(__dirname,'..'),out=path.join(root,'data/q2r1');fs.mkdirSync(out,{recursive:true});assert.equal(cp.execFileSync('git',['rev-parse','HEAD'],{cwd:poc,encoding:'utf8'}).trim(),'4eb684911c5785667181b9d3f940b1dc820e66d1');const status=()=>cp.execFileSync('git',['status','--porcelain'],{cwd:poc,encoding:'utf8'});assert.equal(status(),'');const{loadHost}=require(path.join(poc,'verification/chaos_world_harness.js'));
const keys='state next xu yu vx vy player_flags held pressed move bg contacts modifier previous surface_delta input_delta water support'.split(' '),snap=a=>Object.fromEntries(keys.map(k=>[k,a[k]]));const rows=[];let checks=0;
for(const act of [1,2])for(const width of [256,348])for(const water of [false,true])for(const initial of [-16,16])for(const intent of [-1,1]){
 if(!water&&act===2)continue;
 const h=loadHost(),c=h.ctx,g=h.g;c.room=water?c['ROM_chaos_aqz'+act]:c.ROM_chaos_thz1;c.chaos_level_install_layout();const [x,y]=water?(act===1?[1680,654]:[1136,814]):[160,654];if(water)g.chaosAqzEnv.line=act===1?568:788;h.world.cam.w=width;h.world.cam.h=196;
 const p=h.newPlayer(x,y,{state:5,move:0,bg:2,previous:129,vx:initial});p.image_xscale=Math.sign(initial);p.chaosCore.player_flags=initial<0?16:0;
 const trace=[],events=[];let expectedFace=initial<0?16:0,release=null;
 const orig=c.chaos_visual_p1_present;c.chaos_visual_p1_present=function(o){const before=snap(o.chaosCore),r=orig(o);events.push({writer:'chaos_visual_p1_present',before,after:snap(o.chaosCore),modelFace:o.chaosCore.visual_anim?.pface});return r;};
 for(let n=0;n<24;n++){
  const a=p.chaosCore,input=n===0||n>=5?(intent<0?{left:true}:{right:true}):n===3?{down:true,jump:true,jumpPress:true}:{down:true};events.length=0;const before=snap(a);h.frame(input);
  // Canonical $3783 calls $48A7 while requested state remains5. $45CE also calls it. Flat standing/charge setters preserve this facing.
  if(a.state===5&&a.next===5||a.next===5&&before.next!==5){if(a.held&4)expectedFace=16;else if(a.held&8)expectedFace=0;}
  if(a.state===15&&a.next===16){release={n,actualVX:a.vx,canonicalVX:expectedFace?-1792:1792,face:a.player_flags,expectedFace};assert.equal(Math.abs(a.vx),1792);checks++;}
  trace.push({n,input,before,after:snap(a),canonicalFacingBit:n<=5?expectedFace:null,drawFacing:c.chaos_player_draw_xscale(p),instanceFacing:p.image_xscale,events:events.slice()});
 }
 assert.ok(release,'reaches actual charge/release');checks++;
 rows.push({act:water?act:null,room:water?'aqz'+act:'thz1',width,water,initial,intent,seed:[x,y],placement:'Seeded local player state on unchanged real map, no objects. Low-speed transition slice; not Chief fast-move replay.',release,status:release.actualVX===release.canonicalVX?'proven-match':'proven-gap',trace});
}
assert.equal(status(),'');fs.writeFileSync(path.join(out,'dash-traces.json.gz'),require('zlib').gzipSync(JSON.stringify({method:'Shipped adapter/source host vs reduced facing+release contract from recovered $3783/$45CE/$4719, not new ROM execution',checks,rows})+'\n',{level:9}));console.log(JSON.stringify({checks,cases:rows.length,gaps:rows.filter(r=>r.status==='proven-gap').length,wetGaps:rows.filter(r=>r.water&&r.status==='proven-gap').length,example:rows.find(r=>r.water&&r.status==='proven-gap')?.release}));
