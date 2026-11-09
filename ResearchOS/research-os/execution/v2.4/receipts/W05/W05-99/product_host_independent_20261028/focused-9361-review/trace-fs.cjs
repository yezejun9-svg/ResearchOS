const fs=require('node:fs');
for(const name of ['existsSync','mkdirSync','rmSync']) {
  const original=fs[name];
  fs[name]=function(...args){
    const result=original.apply(this,args);
    if(String(args[0]).includes('runtime')||String(args[0]).endsWith('installed-product.json')) {
      let info;try{const s=fs.lstatSync(args[0]);info={dir:s.isDirectory(),file:s.isFile()}}catch(e){info=e.code}
      process.stderr.write(JSON.stringify({op:name,path:String(args[0]),result,after:info})+'\n');
    }
    return result;
  };
}
