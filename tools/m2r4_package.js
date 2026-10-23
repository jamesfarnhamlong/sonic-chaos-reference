// Read-only execution of actual private C GML. No compiled GPU/Windows claim.
const fs=require('fs'),path=require('path'),assert=require('assert');
const root=path.resolve(__dirname,'..'),pkg=path.resolve(process.argv[2]);
const {loadHost}=require(path.join(pkg,'verification/chaos_world_harness.js'));
const original=JSON.parse(fs.readFileSync(path.join(root,'data/m2r4/original-game.json')));
const pal=JSON.parse(fs.readFileSync(path.join(root,'data/m2r4/palette-original.json')));
const h=loadHost(null),c=h.ctx,g=h.g,w=h.world;
c.array_push=(a,...values)=>a.push(...values); // Native GML permits variadic push; bundled mock only accepts one.
const plain=v=>JSON.parse(JSON.stringify(v));
const out={method:'actual private C GML in existing JS host; shared-call replay from each original input snapshot, not native GPU/Windows',palette:[],shared:[],free_runs:[]};
const fields=['xu','yu','vx','vy','next','move','bg','contacts','water','input_delta','surface_delta','maximum'];
for(const r of pal.skim_controls){
 const e=c.chaos_aqz_env_new(r.act);e.line=[568,788][r.act-1];
 const p=Object.assign(c.SCR_cc_new(816,e.line+r.dy),{character:r.character,water:255,vx:r.vx,vy:r.vy,move:r.attack});
 c.chaos_aqz_cross(e,p,c.chaos_s2_state());assert.deepStrictEqual([p.water,p.vx,p.vy],[r.water,r.result_vx,r.result_vy]);
}
// The drawing calls capture actual selected shader uniforms and resources.
c.chaos_is_aqz=()=>true;c.chaos_aqz_trace=()=>{};
c.draw_sprite_ext=(...args)=>{out.lastDraw=args;};
c.shader_get_uniform=(s,n)=>n;
let uniforms={};c.shader_set_uniform_f=(n,v)=>{uniforms[n]=v;};
c.shader_set_uniform_f_array=(n,v)=>{uniforms[n]=plain(v);};
const sources=c.chaos_aqz_palette_sources();
const fsh=fs.readFileSync(path.join(pkg,'shaders/SHD_chaos_aqz_palette/SHD_chaos_aqz_palette.fsh'),'utf8');
for(const expression of ['floor(col.a*255.0+0.5)-1.0','floor(col.r*255.0+0.5)-1.0',
 'v_world_y-screen_top>=irq_cut','full ? submerged[i] : (lower ? split[i] : (proxy ? col.rgb : above[i]))',
 'vec4(output_rgb,alpha)*v_vColour'])assert(fsh.includes(expression));
out.shader_pixels=[];
for(const k of ['above_water_cram','split_irq_cram','fully_submerged_cram'])assert.deepStrictEqual(plain(sources[k]),pal.sources[k]);
out.palette_histories=[];
for(const history of pal.histories){
 const e=c.chaos_aqz_env_new(1);e.line=568;const rows=[];
 for(const r of history.rows){
  g.chaosAqzEnv=e;c.chaos_aqz_raster(e,e.line-r.delta);w.cam.y=e.line-r.delta;
  uniforms={};c.chaos_aqz_palette_begin(false);
  const upper=uniforms.palette_mode===1?'full':'above';
  rows.push({...r,C_upper:upper,different:upper!==r.upper,C_palette_latch:e.palette});
 }
 out.palette_histories.push({character:history.character,rows});
}
for(const r of pal.boundaries){
 const e=c.chaos_aqz_env_new(r.act);e.line=[568,788][r.act-1];e.enabled=r.prior;e.raster=77;
 g.chaosAqzEnv=e;c.chaos_aqz_raster(e,e.line-r.delta);
 assert.deepStrictEqual([e.enabled,e.raster,plain(e.requests)],[r.enabled,r.raster,r.requests]);
 // For a no-transition startup use above palette, as the original loader does.
 w.cam.y=e.line-r.delta;g.playerWater=false;
 for(const char of [1,2]){
  const sprite=char===2?c.chaos_tails_frame_resource(3,true):c.SPR_sonic_jump;
  const p={sprite_index:sprite,image_index:0,image_xscale:1,image_yscale:1,image_angle:0,image_blend:0xffffff,image_alpha:1,
    x:800,y:e.line,object_index:c.OBJ_player_char,chaosCore:c.SCR_cc_new(800,e.line)};
  uniforms={};c.chaos_aqz_player_draw(p);
  assert.equal(uniforms.player_source,char===2?0:1);
  const row={act:r.act,character:char,delta:r.delta,prior:r.prior,enabled:e.enabled,raster:e.raster,requests:plain(e.requests),
    mode:uniforms.palette_mode,cut:uniforms.irq_cut,screen_top:uniforms.screen_top,decoder:uniforms.player_source,rows:[]};
  for(const sy of [-1,0,1,r.delta,r.delta+1,191,192,193,195]){
   const mode=uniforms.palette_mode;
   const key=mode===1?'submerged':mode===2&&sy>=uniforms.irq_cut?'split':'above';
   row.rows.push({screen_y:sy,lookup:key,rgb_index3:uniforms[key].slice(19*3,20*3).map(x=>Math.round(x*255))});
   const reference=pal.sources[key==='above'?'above_water_cram':key==='split'?'split_irq_cram':'fully_submerged_cram'];
   for(let idx=17;idx<32;idx++){
    const input=char===2?[idx+1,1,1,255]:[...uniforms.above.slice(idx*3,idx*3+3).map(x=>Math.round(x*255)),idx+1];
    const decoded=(char===2?input[0]:input[3])-1;assert.equal(decoded,idx);
    const rgb=uniforms[key].slice(decoded*3,decoded*3+3).map(x=>Math.round(x*255));
    const cram=reference[idx],expected=[(cram&3)*85,((cram>>2)&3)*85,((cram>>4)&3)*85];
    assert.deepStrictEqual(rgb,expected);
    if(r.act===1&&r.prior===255&&r.character===1&&sy===r.delta+1)
      out.shader_pixels.push({character:char,delta:r.delta,screen_y:sy,input,decoded,lookup:key,output:[...rgb,255],
        tint:[0.5,1,0.25,0.5],tinted_output:[rgb[0]*0.5,rgb[1],rgb[2]*0.25,127.5]});
   }
  }
  out.palette.push(row);
 }
}
// AQZ3 normal, no controller and no submerged palette selection.
{const e=c.chaos_aqz_env_new(3);g.chaosAqzEnv=e;c.chaos_aqz_create_water(e,c.chaos_s2_state());
 uniforms={};c.chaos_aqz_palette_begin(false);assert.equal(uniforms.palette_mode,0);
 out.aqz3={mode:uniforms.palette_mode,line:e.line,water_updater:'disabled',normal_above_palette:true};}
for(const f of original.cases){
 c[`SCR_chaos_aqz${f.act}_profiles`]();g.chaosTileIds=c[`SCR_chaos_aqz${f.act}_tile_ids`]();g.chaosMapWidth=f.act===1?168:128;
 g.chaosBeyondMapOpen=false;g.player=f.character;
 const comparisons=[];
 for(const s of f.shared){
  const p=Object.assign(c.SCR_cc_new(0,0),s.before);
  const e=c.chaos_aqz_env_new(f.act);e.line=s.before.line;g.chaosAqzEnv=e;
  const phases=[];const keys=original.phase_columns.slice(2);
  const value=phase=>[s.u,phase,...keys.map(k=>k==='line'?e.line:p[k])];
  const restore=[];
  for(const [fn,phase] of [['SCR_cc_input','input_before'],['SCR_cc_x','x_before'],['SCR_cc_y','y_before'],['SCR_cc_floor','terrain_before']]){
   const old=c[fn];restore.push([fn,old]);c[fn]=(...args)=>{phases.push(value(phase));return old(...args);};
  }
  const cross=c.chaos_aqz_cross;restore.push(['chaos_aqz_cross',cross]);
  c.chaos_aqz_cross=(...args)=>{phases.push(value('water_before'));cross(...args);phases.push(value('water_after'));};
  // Original $3FEF calls $48BC before its fresh-action tail. C supplies that
  // owner elsewhere in the adapter. Preserve that boundary in this comparator.
  const jump=c.SCR_cc_jump;let jumpRequested=false;
  c.SCR_cc_jump=()=>{jumpRequested=true;};c.SCR_cc_shared(p);c.SCR_cc_jump=jump;
  c.SCR_cc_damage_gate(p);if(jumpRequested)jump(p);
  for(const [fn,old] of restore)c[fn]=old;
  const differences={};for(const k of fields)if(p[k]!==s.after[k])differences[k]=[s.after[k],p[k]];
  comparisons.push({u:s.u,original:Object.fromEntries(fields.map(k=>[k,s.after[k]])),C:Object.fromEntries(fields.map(k=>[k,p[k]])),phases,differences});
 }
 out.shared.push({id:f.id,comparisons,mismatches:comparisons.filter(x=>Object.keys(x.differences).length).length});
}
delete out.lastDraw;
// Independent continuous C adapter runs, replaying the original's polled inputs.
// Original camera history is supplied deliberately to isolate width/bounds effects.
// Animation/lifecycle phase is not forced into equivalence after the initial seed.
for(const f of original.cases)for(const width of [256,348]){
 const hh=loadHost(null),cc=hh.ctx,gg=hh.g,ww=hh.world;
 cc.room=cc['ROM_chaos_aqz'+f.act];cc.chaos_level_install_layout();gg.player=f.character;
 cc.chaos_tails_log=()=>{};cc.chaos_tails_diagnostics=()=>{};
 ww.cam.w=width;ww.cam.h=width===256?192:196;ww.follow=false;
 const seed=f.starts[0].core;gg.chaosAqzEnv.line=seed.line;
 const pp=hh.newPlayer(seed.xu/256,seed.yu/256,{state:seed.state,move:seed.move,bg:seed.bg,previous:seed.previous});
 Object.assign(pp.chaosCore,seed);pp.image_xscale=seed.player_flags&16?-1:1;
 cc.SCR_chaos_core_publish(pp);
 const firstShared=[];const sharedFn=cc.SCR_cc_shared;
 cc.SCR_cc_shared=p=>{if(firstShared.length===0)firstShared.push({core:plain(p),lookup:plain(cc.SCR_cc_lookup(p.xu/256,p.yu/256+18,p.plane)),map_width:gg.chaosMapWidth});return sharedFn(p);};
 const rows=[];
 for(let i=0;i<f.rows.length;i++){
  const input=f.starts.find(x=>x.u===i+1).core;
  ww.cam.x=input.camera_x;ww.cam.y=i===0?f.rows[0].core.camera_y:input.camera_y;
  hh.frame({left:!!(input.held&4),right:!!(input.held&8),up:!!(input.held&1),down:!!(input.held&2),
    jump:!!(input.held&48),jumpPress:!!(input.pressed&48)});
  const p=pp.chaosCore;rows.push({u:i+1,xu:p.xu,yu:p.yu,vx:p.vx,vy:p.vy,state:p.state,next:p.next,
   move:p.move,water:p.water,held:p.held,pressed:p.pressed,jump_ticks:p.jump_ticks,
   face:p.player_flags&16,camera_x:ww.cam.x,camera_y:ww.cam.y,input_delta:p.input_delta,
   surface_delta:p.surface_delta,contacts:p.contacts,dead:!!pp.dead});
 }
 const keys=['xu','yu','vx','vy','state','next','move','water','jump_ticks'];
 const differences=[];
 for(let i=0;i<rows.length;i++){
  const delta={};for(const k of keys)if(rows[i][k]!==f.rows[i].core[k])delta[k]=[f.rows[i].core[k],rows[i][k]];
  if(Object.keys(delta).length)differences.push({u:i+1,fields:delta});
 }
 out.free_runs.push({id:f.id,width,initial_shared:firstShared,rows,differences,first_difference:differences[0]||null});
}
out.summary={palette_conditions:out.palette.length,shared_calls:out.shared.reduce((n,x)=>n+x.comparisons.length,0),
 shared_mismatches:out.shared.reduce((n,x)=>n+x.mismatches,0),continuous_adapter_runs:out.free_runs.length,
 continuous_fully_matching:out.free_runs.filter(x=>x.differences.length===0).length,skim_controls:pal.skim_controls.length};
fs.writeFileSync(path.join(root,'data/m2r4/package-comparison.json'),JSON.stringify(out)+'\n');
console.log(JSON.stringify(out.summary));
