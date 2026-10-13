import fs from 'node:fs';
const mode=process.argv[2];
if(!['enable','reset'].includes(mode))throw new Error('Use enable or reset');
const file='public/cart.js';const good='return price * quantity;';const bad='return quantity > 0 ? price : 0;';
const src=fs.readFileSync(file,'utf8');
if(!src.includes(good)&&!src.includes(bad))throw new Error('Implementation changed. Inspect before modifying.');
fs.writeFileSync(file,src.replace(mode==='enable'?good:bad,mode==='enable'?bad:good));
console.log(mode==='enable'?'Cart quantity bug enabled. Regression tests should fail.':'Working cart restored.');
