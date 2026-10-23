// Read-only execution of accepted opening GML. No GameMaker/native claim.
const fs=require('fs'),vm=require('vm'),path=require('path'),crypto=require('crypto');
const root=process.argv[2];if(!root)throw Error('pass accepted POC checkout');
const rel='scripts/SCR_chaos_opening/SCR_chaos_opening.gml';
const source=fs.readFileSync(path.join(root,rel),'utf8');
const ctx=vm.createContext({min:Math.min,max:Math.max,floor:Math.floor});
vm.runInContext(source.replace(/^#macro (\w+) (.*)$/gm,'var $1=$2;'),ctx);
const rows=[];
for(const skip of [null,1,2,70,300,600,738]){
 const s=ctx.chaos_opening_new();let end=null,hand=null;
 for(let tick=1;tick<900;tick++){
  ctx.chaos_opening_step(s,tick===skip);
  if(s.post&&end===null)end=tick;
  if(s.done){hand=tick;break;}
 }
 if(hand-end!==40)throw Error('opening post duration changed');
 rows.push({skip_press_tick:skip,post_entry_tick:end,title_handoff_tick:hand,
  proposed_audio_fade_tick:hand-33,proposed_reset_tick:hand-11});
}
console.log(JSON.stringify({evidence:'executed accepted opening GML in node VM; no native run',
 source:rel,utf8_source_sha256:crypto.createHash('sha256').update(source).digest('hex'),
 ticks_are:'1-based host Step calls; fade applied before indicated audio tick',rows},null,2));
