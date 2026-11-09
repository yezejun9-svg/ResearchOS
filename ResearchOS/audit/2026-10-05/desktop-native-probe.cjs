// Native Electron entrypoint audit. Catches startup failure before Electron opens its error dialog.
const { app } = require('electron');
const path = require('node:path');
function report(error) {
  console.log(JSON.stringify({scope:'NATIVE_ELECTRON_ENTRYPOINT',electron:process.versions.electron, error:String(error),stack:error?.stack}));
  app.exit(2);
}
process.on('uncaughtException',report);
try { require(path.resolve(__dirname,'../../research-os/apps/desktop/main/main.js')); }
catch(error) { report(error); }
