// Run existing accepted-POC verifiers without writing into the POC.
const fs=require('fs'),path=require('path'),cp=require('child_process');
if(process.env.C2R1_CHILD){
 const src=path.resolve(process.env.C2R1_POC),dst=path.resolve(process.env.C2R1_OUT);
 const redirect=p=>{p=path.resolve(String(p));if(p===src||p.startsWith(src+path.sep))return path.join(dst,path.relative(src,p));if(p===dst||p.startsWith(dst+path.sep))return p;throw Error('Out-of-scope write: '+p);};
 const mkdir=fs.mkdirSync.bind(fs),write=fs.writeFileSync.bind(fs);
 fs.mkdirSync=(p,o)=>mkdir(redirect(p),o);
 fs.writeFileSync=(p,...args)=>{const target=redirect(p);mkdir(path.dirname(target),{recursive:true});return write(target,...args);};
}else{
 const poc=path.resolve(process.argv[2]||'../SonicChaos_POC_c2e1'),out=path.resolve(__dirname,'../data/q2r1/gate');fs.mkdirSync(out,{recursive:true});
 const assert=require('assert');assert.equal(cp.execFileSync('git',['rev-parse','HEAD'],{cwd:poc,encoding:'utf8'}).trim(),'4eb684911c5785667181b9d3f940b1dc820e66d1');assert.equal(cp.execFileSync('git',['status','--porcelain'],{cwd:poc,encoding:'utf8'}),'');
 const tests=['verify_monitor_support.js'];
 const results=[];
 for(const test of tests){const start=Date.now();const r=cp.spawnSync(process.execPath,['-r',__filename,path.join(poc,'verification',test)],{cwd:poc,encoding:'utf8',timeout:45000,maxBuffer:8*1024*1024,env:{...process.env,C2R1_CHILD:'1',C2R1_POC:poc,C2R1_OUT:out}});
 fs.writeFileSync(path.join(out,test+'.log'),(r.stdout||'')+(r.stderr||''));const row={test,status:r.status,signal:r.signal,error:r.error?.message,ms:Date.now()-start};results.push(row);console.log(JSON.stringify(row));}
 fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');
 assert.equal(cp.execFileSync('git',['status','--porcelain'],{cwd:poc,encoding:'utf8'}),'');if(results.some(r=>r.status!==0))process.exitCode=1;
}
