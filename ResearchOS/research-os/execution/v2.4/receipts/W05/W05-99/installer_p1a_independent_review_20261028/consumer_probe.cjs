'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const p = require('./product-layout.js');
const out = [];
for (const root of process.argv.slice(2)) {
  const layout = p.loadProductLayout(root);
  assert.equal(layout.installID, p.installationIdentity(layout.marker));
  assert.equal(layout.inventoryDigest, p.inventoryIdentity(layout.marker.files));
  out.push({root, installationID:layout.installID, inventory:layout.inventoryDigest, files:layout.marker.files.length});
}
assert.notEqual(out[0].installationID,out[1].installationID);
assert.equal(fs.existsSync(process.env.LOCALAPPDATA+'/ResearchOS'),false);
console.log(JSON.stringify({status:'READ_ONLY_PRODUCT_LOADER_PASS',roots:out,productProcessRuns:0,dataWrites:0},null,2));
