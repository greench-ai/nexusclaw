const fs = require('fs');
const v = Date.now().toString(36);
let h = fs.readFileSync('dist/index.html', 'utf8');
// Replace ./assets/index-HASH.js" with ./assets/index-HASH.js?v=VERSION"
h = h.replace(/(\.\/assets\/index-[a-zA-Z0-9]+\.js)"/g, '$1?v=' + v + '"');
h = h.replace(/(\.\/assets\/index-[a-zA-Z0-9]+\.css)"/g, '$1?v=' + v + '"');
fs.writeFileSync('dist/index.html', h);
console.log('Cache-bust v=' + v);
