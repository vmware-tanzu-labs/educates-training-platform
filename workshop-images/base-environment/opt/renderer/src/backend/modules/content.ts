import * as fs from "fs"
import * as path from "path"
import { marked } from "marked"
import * as _s from "underscore.string"
import { Liquid } from "liquidjs"

let asciidoctor = require("asciidoctor")()

import { config } from "./config"

// Generic functions.

function slug_to_title(slug) {
    return _s.titleize(_s.humanize(path.basename(slug)))
}

function replace_variables(data, variables) {
    variables.forEach((v) => {
        data = data.replace(new RegExp("%" + v.name + "%", "g"), v.content)
    })

    return data
}

async function render_liquidjs(data, variables) {
    let options = {
        root: config.content_dir
    }

    let engine = new Liquid(options)

    let params = {}

    variables.forEach((v) => {
        params[v.name] = v.content
    })

    return await engine.parseAndRender(data, params)
}

// Page navigation.

export function modules() {
    // Use provided page index if one exists. Generate all the prev and next
    // links before returning.

    let modules = []
    let count = 0

    if (config.modules !== undefined && config.modules.length > 0) {
        let temp_modules = config.modules.slice(0)
        let page = temp_modules.shift()

        while (page !== undefined) {
            count = count + 1

            if (page.title === undefined) {
                page.title = slug_to_title(page.path)
            }

            if (page.file === undefined) {
                let file = path.join(config.content_dir, page.path) + ".md"

                if (fs.existsSync(file)) {
                    page.file = file
                    page.format = "markdown"
                    page.fences = "hljs"
                }
            }

            if (page.file === undefined) {
                let file = path.join(config.content_dir, page.path) + ".adoc"

                if (fs.existsSync(file)) {
                    page.file = file
                    page.format = "asciidoc"
                    page.fences = ""
                }
            }

            if (temp_modules.length > 0) {
                page.next_page = temp_modules[0].path
                temp_modules[0].prev_page = page.path
            }

            page.step = count

            modules.push(page)
            page = temp_modules.shift()
        }
    }

    return modules
}

export function module_index(modules) {
    let index = {}

    modules.forEach((page) => index[page.path] = page)

    return index
}

// Markdown rendering.

let marked_renderer = new marked.Renderer()

marked.setOptions({
    renderer: marked_renderer,
    highlight: function(code, lang) {
        const hljs = require('highlight.js/lib/common');
        const language = hljs.getLanguage(lang) ? lang : 'plaintext';
        return hljs.highlight(code, { language }).value;
      },
    langPrefix: 'hljs language-',
    pedantic: false,
    gfm: true,
    breaks: false,
    sanitize: false,
    smartLists: true,
    smartypants: false,
    xhtml: false
})

async function markdown_process_page(file, pathname, variables) {
    let data = fs.readFileSync(file).toString("utf-8")

    data = await render_liquidjs(data, variables)

    // Support for %variable% is for backward compatibility only.

    data = replace_variables(data, variables)

    return marked(data)
}

// Asciidoc rendering.

async function asciidoc_process_page(file, pathname, variables) {
    let data = fs.readFileSync(file).toString("utf-8")

    data = await render_liquidjs(data, variables)

    // Support for %variable% is for backward compatibility only.
    
    data = replace_variables(data, variables)

    let attributes = {}

    let doc = asciidoctor.load(data, { safe: "server", attributes: { attributes } })

    return doc.convert()
}

// Entrypoint for rendering.

export async function render(module, variables) {
    let file = module.file
    var pathname = module.path

    if (file) {
        if (module.format == "markdown")
            return await markdown_process_page(file, pathname, variables)

        if (module.format == "asciidoc")
            return await asciidoc_process_page(file, pathname, variables)

        return
    }

    file = path.join(config.content_dir, pathname + ".md")

    if (fs.existsSync(file))
        return await markdown_process_page(file, pathname, variables)

    file = path.join(config.content_dir, pathname + ".adoc")

    if (fs.existsSync(file))
        return await asciidoc_process_page(file, pathname, variables)
}
