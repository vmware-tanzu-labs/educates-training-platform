var fs = require('fs');
var YAML = require('js-yaml');

var text = fs.readFileSync(0, 'utf-8');
var data = YAML.safeLoad(text);

console.info(JSON.stringify(data, null, '  '));
