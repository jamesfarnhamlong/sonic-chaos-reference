const fs=require('fs'),path=require('path'),crypto=require('crypto');
const pkg=path.resolve(process.argv[2]);
const {loadHost}=require(path.join(pkg,'verification/chaos_world_harness.js'));
const rows=[];
for(const [act,zone,width,y] of [[4,'gpz1',5120,430.4296875],[5,'gpz2',4096,686.25],[10,'mghz1',4096,366.4375],[16,'eez1',4096,430.671875]]){
 const h=loadHost(null),c=h.ctx,g=h.g;c.room=c['ROM_chaos_'+zone];c.chaos_level_install_layout();
 for(const offset of [11,10,9]){
  const p=c.SCR_cc_new();p.xu=(width-offset)*256+16;p.yu=y*256;p.bg=2;p.contacts=2;p.state=5;
  const probe=c.SCR_cc_lookup(Math.floor(p.xu/256)+9,Math.floor(p.yu/256)+6,0);
  c.SCR_cc_sides(p);rows.push({act,offset,probe,x_after:p.xu/256,bg:p.bg,contacts:p.contacts});
 }
}
const files=['SCR_chaos_core','SCR_chaos_adapter','SCR_chaos_camera','SCR_chaos_goal','SCR_chaos_tails'];
const sources=files.map(n=>({script:n,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(pkg,'scripts',n,n+'.gml'))).digest('hex')}));
fs.writeFileSync(path.join(__dirname,'../data/m2r5/package-controls.json'),JSON.stringify({evidence:'actual shipped GML source-host, local contact fixture; NOT natural route',rows,sources},null,2)+'\n');
console.log(rows.map(r=>[r.act,r.offset,r.probe.tile,r.bg]));
