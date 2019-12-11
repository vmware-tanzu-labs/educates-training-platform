var fs = require('fs');
var path = require('path');
var yaml = require('js-yaml');
var rp = require('request-promise');

var workshop_dir = process.argv[2]
var download_url = process.argv[3]
var workshop_file = process.argv[4]

if (!download_url) {
    console.log('Invalid workshop download URL provided.');
    process.exit(1);
}

console.log('Download URL:', download_url);

async function main() {
    // First download the workshop file. The name will depend on
    // whether looking at legacy Workshopper content or new
    // Homeroom content. Try _workshop.yml first which is what
    // legacy Workshopper content would use.

    var workshop_url;
    var workshop_body;

    if (workshop_file) {
        workshop_url = download_url + '/' + workshop_file;

        workshop_body = await rp(workshop_url).then((body) => {
            console.log('Downloaded:', workshop_url);
            return body;
        }).catch((err) => {
            console.log('Failed to download workshop file.', err);
            process.exit(1);
        });
    }
    else {
        workshop_url = download_url + '/_workshop.yml';

        workshop_body = await rp(workshop_url).then((body) => {
            console.log('Downloaded:', workshop_url);
            return body;
        }).catch((err) => {
            return;
        });

        if (workshop_body === undefined) {
            workshop_url = download_url + '/workshop.yaml';

            workshop_body = await rp(workshop_url).then((body) => {
                console.log('Downloaded:', workshop_url);
                return body;
            }).catch((err) => {
                console.log('Failed to download workshop file.', err);
                process.exit(1);
            });
        }
    }

    // Download the config.js file if one exists and save it. It is
    // assumed that even if this is provided, that list of modules is
    // given by the workshop file.

    try {
        fs.mkdirSync(workshop_dir, { recursive: true });
    }
    catch (err) {
        if (err.code != 'EEXIST') {
            console.log('Unable to create workshop directory.', err);
            process.exit(1);
        }
    }

    var config_url;
    var config_body;
    
    config_url = download_url + '/config.js';

    config_body = await rp(config_url).then((body) => {
        console.log('Downloaded:', config_url);
        return body;
    }).catch((err) => {
        return;
    });

    if (config_body) {
        fs.writeFileSync(path.join(workshop_dir, 'config.js'), config_body);
    }

    // Save the workshop file as workshop.yaml. If there is a config.js
    // we want to use the same name file as may have been supplied.
    // In that case it cannot be in a sub directory.

    if (config_body) {
        workshop_file = workshop_file || 'workshop.yaml';
    }
    else {
        workshop_file = 'workshop.yaml';
    }

    fs.writeFileSync(path.join(workshop_dir, workshop_file), workshop_body);

    // Now download the modules file. The name will depend on
    // whether looking at legacy Workshopper content or new
    // Homeroom content. Try _modules.yml first which is what
    // legacy Workshopper content would use.

    var modules_file;
    var modules_url;
    var modules_body;

    var legacy_mode = true;

    modules_file = '_modules.yml';
    modules_url = download_url + '/' + modules_file;

    modules_body = await rp(modules_url).then((body) => {
        console.log('Downloaded:', modules_url);
        return body;
    }).catch((err) => {
        return;
    });

    if (modules_body === undefined) {
        modules_file = 'modules.yaml';
        modules_url = download_url + '/' + modules_file;

        legacy_mode = false;

        modules_body = await rp(modules_url).then((body) => {
            console.log('Downloaded:', modules_url);
            return body;
        }).catch((err) => {
            console.log('Failed to download modules file.', err);
            process.exit(1);
        });
    }

    // We want to flag the template engine as liquid.js if this
    // is legacy Workshopper content. We also need to set up the
    // remote location for downloading images.

    var modules_data = yaml.safeLoad(modules_body);

    if (!modules_data.config) {
        modules_data.config = {}
    }

    if (legacy_mode) {
        modules_data.config.template_engine = 'liquid.js';
        modules_data.config.images_url = download_url + '/images';
    }
    else {
        modules_data.config.images_url = download_url + '/content';
    }

    modules_body = yaml.safeDump(modules_data);

    // Save the modules file as modules.yaml.

    fs.writeFileSync(path.join(workshop_dir, 'modules.yaml'), modules_body);

    // Next we need to download each of the workshop content
    // files. If workshop is legacy Workshopper content, the
    // files are in the top level directory, otherwise expect
    // them to be in the content sub directory.

    try {
        fs.mkdirSync(path.join(workshop_dir, 'content'), { recursive: true });
    }
    catch (err) {
        if (err.code != 'EEXIST') {
            console.log('Unable to create content directory.', err);
            process.exit(1);
        }
    }

    var workshop_data = yaml.safeLoad(workshop_body);

    var modules = workshop_data.modules.activate;

    for (let i = 0; i < modules.length; i++) {
        let module_url;
        let module_body;

        // First try AsciiDoc files.

        if (!legacy_mode) {
            module_url = download_url + '/content/' + modules[i] + '.adoc';
        }
        else {
            module_url = download_url + '/' + modules[i] + '.adoc';
        }

        module_body = await rp(module_url).then((body) => {
            console.log('Downloaded:', module_url);
            return body;
        }).catch((err) => {
            return;
        });

        if (module_body) {
            let module_file = path.join(workshop_dir, 'content',
                    modules[i] + '.adoc');
            let module_dir = path.dirname(module_file);

            try {
                fs.mkdirSync(module_dir, { recursive: true });
            }
            catch (err) {
                if (err.code != 'EEXIST') {
                    console.log('Unable to create module parent directory.', err);
                    process.exit(1);
                }
            }

            fs.writeFileSync(module_file, module_body);

            continue;
        }

        // Next try Markdown fils.

        if (!legacy_mode) {
            module_url = download_url + '/content/' + modules[i] + '.md';
        }
        else {
            module_url = download_url + '/' + modules[i] + '.md';
        }

        module_body = await rp(module_url).then((body) => {
            console.log('Downloaded:', module_url);
            return body;
        }).catch((err) => {
            return;
        });

        if (module_body !== undefined) {
            let module_file = path.join(workshop_dir, 'content',
                    modules[i] + '.md');
            let module_dir = path.dirname(module_file);

            try {
                fs.mkdirSync(module_dir, { recursive: true });
            }
            catch (err) {
                if (err.code != 'EEXIST') {
                    console.log('Unable to create module parent directory.', err);
                    process.exit(1);
                }
            }

            fs.writeFileSync(module_file, module_body);

            continue;
        }
    }
}

main();
