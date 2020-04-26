var fs = require('fs');
var path = require('path');
var yaml = require('js-yaml');
var marked = require('marked');
var asciidoctor = require('asciidoctor')();
var _s = require('underscore.string');
var Liquid = require('liquidjs');

var config = require('./config.js');

// Generic functions.

function slug_to_title(slug) {
    return _s.titleize(_s.humanize(path.basename(slug)));
}

function replace_variables(data, variables) {
    variables.forEach((v) => {
        data = data.replace(new RegExp('%'+v.name+'%', 'g'), v.content);
    });

    return data;
}

async function render_liquidjs(data, variables) {
    var options = {
        root: config.content_dir,
    };

    var engine = new Liquid(options);

    var params = {};

    variables.forEach((v) => {
        params[v.name] = v.content;
    });

    return await engine.parseAndRender(data, params);
}

// Page navigation.

function modules() {
    // Use provided page index if one exists. Generate all the
    // prev and next links before returning.

    var modules = []
    var count = 0;

    if (config.modules !== undefined && config.modules.length > 0) {
        let temp_modules = config.modules.slice(0);
        let page = temp_modules.shift();

        while (page !== undefined) {
            count = count + 1;

            if (page.title === undefined) {
                page.title = slug_to_title(page.path);
            }

            if (page.file === undefined) {
                let file = path.join(config.content_dir, page.path) + '.md';

                if (fs.existsSync(file)) {
                    page.file = file;
                    page.format = 'markdown';
                }
            }

            if (page.file === undefined) {
                let file = path.join(config.content_dir, page.path) + '.adoc';

                if (fs.existsSync(file)) {
                    page.file = file;
                    page.format = 'asciidoc';
                }
            }

            if (temp_modules.length > 0) {
                page.next_page = temp_modules[0].path;
                temp_modules[0].prev_page = page.path;
            }

            page.step = count;

            modules.push(page);
            page = temp_modules.shift();
        }

        return modules;
    }

    // See if the default page is Markdown. If it then we can
    // try and generate the navigation path from page meta data.
    // It is assumed that all pages are Markdown. This is done
    // to provide backward compatibility for when had to use
    // page meta data to specify title and navigation path.

    var pathname = config.default_page;
    var file = path.join(config.content_dir, pathname + '.md');

    if (!fs.existsSync(file)) {
        return [];
    }

    var visited = new Set();

    // Add the default page to the page index.

    var data = fs.readFileSync(file).toString('utf-8');

    var meta = markdown_extract_metadata(data);
    var title = meta.title ? meta.title : slug_to_title(pathname);

    count = count + 1;

    var details = {
      file: file,
      format: 'markdown',
      step: count,
      path: pathname,
      title: title,
      prev_page: null,
      next_page: null,
      exit_sign: meta.exit_sign,
      exit_link: meta.exit_link,
    };

    modules.push(details);
    visited.add(pathname);

    // Traverse the pages to find list of all modules.

    while (meta.next_page) {
        if (visited.has(meta.next_page)) {
            return modules;
        }

        pathname = path.join(path.dirname(pathname), meta.next_page);
        file = path.join(config.content_dir, pathname + '.md');

        if (!fs.existsSync(file)) {
            return modules;
        }

        data = fs.readFileSync(file).toString('utf-8');

        meta = markdown_extract_metadata(data);
        title = meta.title ? meta.title : slug_to_title(pathname);

        modules[modules.length-1].next_page = pathname;

        count = count + 1;

        details = {
          file: file,
          format: 'markdown',
          step: count,
          path: pathname,
          title: title,
          prev_page: modules[modules.length-1].path,
          next_page: null,
          exit_sign: meta.exit_sign,
          exit_link: meta.exit_link,
        };

        modules.push(details);
    }

    return modules;
}

function module_index(modules) {
    var index = {}

    modules.forEach(page => index[page.path] = page);

    return index;
}

// Markdown rendering.

marked_renderer = new marked.Renderer();

marked.setOptions({
  renderer: marked_renderer,
  pedantic: false,
  gfm: true,
  tables: true,
  breaks: false,
  sanitize: false,
  smartLists: true,
  smartypants: false,
  xhtml: false
});

const markdown_metadata_regex = /^\uFEFF?---([\s\S]*?)---/i;

function markdown_cleanup_field_name(field, use_underscore) {
    const u = use_underscore || false;

    field = field.replace(/\//g, ' ').trim();

    if (u) {
        return _s.underscored(field);
    }
    else {
        return _s.trim(_s.dasherize(field), '-');
    }
}

function markdown_extract_metadata_fields(obj) {
    let fields = {};

    for (let field in obj) {
        if (obj.hasOwnProperty(field)) {
            let name = markdown_cleanup_field_name(field, true);
            fields[name] = ('' + obj[field]).trim();
        }
    }

    return fields;
}

function markdown_extract_metadata(data) {
    var meta = {};

    if (markdown_metadata_regex.test(data)) {
        let meta_array = data.match(markdown_metadata_regex);
        let meta_string = meta_array ? meta_array[1].trim() : '';
        let yaml_object = yaml.safeLoad(meta_string);

        meta = markdown_extract_metadata_fields(yaml_object);
    }

    return meta;
}

function markdown_extract_content(data) {
    return data.replace(markdown_metadata_regex, '').trim();
}

async function markdown_process_page(file, pathname, variables) {
    var data = fs.readFileSync(file).toString('utf-8');

    data = markdown_extract_content(data);

    data = await render_liquidjs(data, variables);
    data = replace_variables(data, variables);

    return marked(data, { pathname: pathname });
}

// Asciidoc rendering.

async function asciidoc_process_page(file, pathname, variables) {
    var data = fs.readFileSync(file).toString('utf-8');

    data = await render_liquidjs(data, variables);
    data = replace_variables(data, variables);

    let attributes = {}

    var doc = asciidoctor.load(data,
            { safe: 'server', attributes: attributes });

    return doc.convert();
}

// Entrypoint for rendering.

async function render(module, variables) {
    var file = module.file;
    var pathname = module.path;

    if (file) {
        if (module.format == 'markdown') {
            return await markdown_process_page(file, pathname, variables);
        }

        if (module.format == 'asciidoc') {
            return await asciidoc_process_page(file, pathname, variables);
        }

        return;
    }

    file = path.join(config.content_dir, pathname + '.md');

    if (fs.existsSync(file)) {
        return await markdown_process_page(file, pathname, variables);
    }

    file = path.join(config.content_dir, pathname + '.adoc');

    if (fs.existsSync(file)) {
        return await asciidoc_process_page(file, pathname, variables);
    }
}

// Exports.

exports.default = {
    modules,
    module_index,
    render,
}

module.exports = exports.default;
