import * as path from "path"
import * as yaml from "js-yaml"
import * as $ from "jquery"
import "bootstrap"

declare var gtag: Function

function set_paste_buffer_to_text(text) {
    let tmp = $("<textarea>").appendTo("body").val(text).select()
    document.execCommand("copy")
    tmp.remove()
}

function select_element_text(element) {
    let doc = window.document, selection, range
    if (window.getSelection && doc.createRange) {
        selection = window.getSelection()
        range = doc.createRange()
        range.selectNodeContents(element)
        selection.removeAllRanges()
        selection.addRange(range)
    } else if ((<any>doc.body).createTextRange) {
        range = (<any>doc.body).createTextRange()
        range.moveToElementText(element)
        range.select()
    }
}

interface Terminals {
    execute_in_terminal(command: string, id: string): void
    execute_in_all_terminals(command: string): void
    reload_terminals(): void
}

interface Dashboard {
    expose_dashboard(name: string): void
    reload_dashboard(name: string): void
    collapse_workshop(): void
    reload_workshop(): void
    finished_workshop(): void
    preview_image(src: string, title: string): void
}

class Editor {
    readonly retries = 15
    readonly retry_delay = 1000

    private url: string = null

    constructor() {
        let $body = $("body")

        let session_namespace = $body.data('session-namespace')
        let ingress_domain = $body.data('ingress-domain')
        let ingress_protocol = $body.data('ingress-protocol')

        if (session_namespace && ingress_domain && ingress_protocol)
            this.url = `${ingress_protocol}://${session_namespace}.${ingress_domain}/code-server`
    }

    private execute_call(endpoint, data, done, fail) {
        if (!this.url)
            return

        let retries = this.retries
        let retry_delay = this.retry_delay
        let url = this.url + endpoint

        function attempt_call() {
            $.ajax({
                type: 'POST',
                url: url,
                data: data,
                contentType: "application/json",
                dataType: "text"
            })
                .done(() => done())
                .fail((error) => {
                    if (error.status == 504) {
                        if (retries--)
                            setTimeout(attempt_call, retry_delay)
                        else
                            fail("Failed after retries")
                    }
                    else
                        fail("Unexpected HTTP error")
                })
        }

        attempt_call()
    }

    private fixup_path(file: string) {
        if (file.startsWith("~/"))
            file = file.replace("~/", "/home/eduk8s/")
        else if (!file.startsWith("/"))
            file = path.join("/home/eduk8s", file)
        return file
    }

    open_file(file: string, line: number = 1, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, line })
        this.execute_call("/editor/line", data, done, fail)
    }

    append_lines_to_file(file: string, value: string, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, paste: value })
        this.execute_call("/editor/paste", data, done, fail)
    }

    insert_lines_before_line(file: string, line: number, value: string, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, line, paste: value })
        this.execute_call("/editor/paste", data, done, fail)
    }

    append_lines_after_text(file: string, text: string, value: string, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, prefix: text, paste: value })
        this.execute_call("/editor/paste", data, done, fail)
    }

    insert_value_into_yaml(file: string, path: string, value: any, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        if (!path)
            return fail("No property path provided")

        if (value === undefined)
            return fail("No property value provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, yamlPath: path, paste: yaml.safeDump(value) })
        this.execute_call("/editor/paste", data, done, fail)
    }

    execute_command(command: string, args: string[], done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!command)
            return fail("No command provided")

        let data = JSON.stringify(args)
        this.execute_call("/command/" + encodeURIComponent(command), data, done, fail)
    }
}

export let terminals: Terminals
export let dashboard: Dashboard
export let editor: Editor

export function execute_in_terminal(command: string, id: string = "1") {
    if (dashboard && terminals) {
        dashboard.expose_dashboard("terminal")

        id = id || "1"

        if (id == "*")
            terminals.execute_in_all_terminals(command)
        else
            terminals.execute_in_terminal(command, id)
    }
}

export function execute_in_all_terminals(command: string) {
    if (dashboard && terminals) {
        dashboard.expose_dashboard("terminal")
        terminals.execute_in_all_terminals(command)
    }
}

export function reload_terminals() {
    if (dashboard && terminals) {
        dashboard.expose_dashboard("terminal")
        terminals.reload_terminals()
    }
}

export function expose_dashboard(name: string) {
    if (dashboard)
        dashboard.expose_dashboard(name)
}

export function reload_dashboard(name: string) {
    if (dashboard)
        dashboard.reload_dashboard(name)
}

export function collapse_workshop() {
    if (dashboard)
        dashboard.collapse_workshop()
}

export function reload_workshop() {
    if (dashboard)
        dashboard.reload_workshop()
}

export function finished_workshop() {
    if (dashboard)
        dashboard.finished_workshop()
}

function preview_image(src: string, title: string) {
    if (!dashboard) {
        $("#preview-image-element").attr("src", src)
        $("#preview-image-title").text(title)
        $("#preview-image-dialog").modal("show")
    }
    else
        dashboard.preview_image(src, title)
}

export function register_action(name: string, glyph: string, title: any, body: any, handler: any) {
    name = name.replace(":", "\\:")

    let selectors = []

    if ($("body").data("page-format") == "asciidoc")
        selectors = [`.${name} .content code`]
    else
        selectors = [`code.language-${name}`]

    for (let selector of selectors) {
        $(selector).each((_, element) => {
            let code_element = $(element)
            let parent_element = code_element.parent()
            let args = yaml.load(code_element.text().trim() || "{}")

            let title_string = title

            if (typeof title === "function")
                title_string = title(args)

            let title_element = $("<div class='magic-code-block-title'></div>").text(title_string)
            let glyph_element = $(`<span class='magic-code-block-glyph fas fa-${glyph}' aria-hidden='true'></span>`)

            parent_element.before(title_element)
            title_element.prepend(glyph_element)

            let body_string = body

            if (typeof body === "function")
                body_string = body(args)

            if (typeof body_string != "string")
                body_string = ""

            code_element.text(body_string)

            $.each([title_element, parent_element], (_, target) => {
                target.click((event) => {
                    if (!event.shiftKey) {
                        handler(args, () => {
                            title_element.removeClass("bg-danger")
                            glyph_element.removeClass(`fa-${glyph}`)
                            glyph_element.addClass("fa-check-circle")
                        }, (error) => {
                            console.log(`[${title_string}] ${error}`)
                            title_element.addClass("bg-danger")
                        })
                    }
                    else {
                        set_paste_buffer_to_text(body_string)
                    }
                })
            })
        })
    }
}

$(document).ready(() => {
    if (parent) {
        if ((<any>parent).eduk8s) {
            terminals = (<any>parent).eduk8s.terminals
            dashboard = (<any>parent).eduk8s.dashboard
        }
    }

    editor = new Editor()

    let $body = $("body")

    let page_format = $body.data("page-format")

    // Set up page navigation buttons in header and at bottom of pages.

    $("button[data-goto-page]").each((_, element) => {
        if ($(element).data("goto-page")) {
            $(element).removeAttr("disabled")
            $(element).click(() => {
                location.href = path.join("/workshop/content", $(element).data("goto-page"))
            })
        }
        else {
            $(element).removeClass("fa-inverse")
        }
    })

    $("#next-page").click((event) => {
        let next_page = $(event.target).data("next-page")
        let exit_link = $(event.target).data("exit-link")
        let restart_url = $(event.target).data("restart-url")

        if (next_page)
            location.href = path.join("/workshop/content", next_page)
        else if (exit_link)
            location.href = exit_link
        else if (!restart_url || !dashboard)
            location.href = "/workshop/content/"
        else
            finished_workshop()
    })

    // Ensure clicking on links in content always opens them in a new page
    // if they are for an external site.

    $("section.page-content a").each((_, element) => {
        let anchor = <HTMLAnchorElement>element
        if (!(location.hostname === anchor.hostname || !anchor.hostname.length)) {
            $(anchor).attr("target", "_blank")
        }
    })

    // When click on embedded image in content, open it up in image preview
    // dialog so can get a larger view of the image.

    $("section.page-content img").each((_, element) => {
        let image = <HTMLImageElement>element
        $(element).click(() => {
            preview_image(image.src, image.alt)
        })
    })

    // Add markup and click handlers to executable and copyable code.
    // Luckily the markdown and AsciiDoc HTML structures are similar
    // enough that can use the same code for both when use appropriate
    // selectors to match code block. 

    let execute_selectors = []

    if (page_format == "asciidoc") {
        execute_selectors = [
            [".execute .content code", ""],
            [".execute-1 .content code", "1"],
            [".execute-2 .content code", "2"],
            [".execute-3 .content code", "3"],
            [".execute-all .content code", "*"]
        ]
    }
    else {
        execute_selectors = [
            ["code.language-execute", ""],
            ["code.language-execute-1", "1"],
            ["code.language-execute-2", "2"],
            ["code.language-execute-3", "3"],
            ["code.language-execute-all", "*"]
        ]
    }

    if (terminals) {
        for (let [selector, id] of execute_selectors) {
            $(selector).each((_, element) => {
                let parent = $(element).parent()
                let glyph = $(`<span class='magic-code-block-glyph fas fa-running' aria-hidden='true'><sup><sup>${id}</sup></sup></span>`)
                parent.prepend(glyph)
                parent.click((event) => {
                    let command = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                    if (!event.shiftKey) {
                        glyph.removeClass("fa-running")
                        glyph.addClass("fa-check-circle")
                        execute_in_terminal(command, id)
                    }
                    else {
                        set_paste_buffer_to_text(command)
                    }

                    /* select_element_text(event.target) */
                })
            })
        }
    }
    else {
        for (let [selector, id] of execute_selectors) {
            $(selector).each((_, element) => {
                let parent = $(element).parent()
                let glyph = $("<span class='magic-code-block-glyph fas fa-copy' aria-hidden='true'></span>")
                parent.prepend(glyph)
                parent.click((event) => {
                    let command = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                    glyph.removeClass("fa-copy")
                    glyph.addClass("fa-check-circle")
                    set_paste_buffer_to_text(command)
                    /* select_element_text(event.target) */
                })
            })
        }
    }

    let copy_selectors = []

    if (page_format == "asciidoc")
        copy_selectors = [".copy .content code"]
    else
        copy_selectors = ["code.language-copy"]

    for (let selector of copy_selectors) {
        $(selector).each((_, element) => {
            let parent = $(element).parent()
            let glyph = $("<span class='magic-code-block-glyph fas fa-copy' aria-hidden='true'></span>")
            parent.prepend(glyph)
            parent.click((event) => {
                let text = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                glyph.removeClass("fa-copy")
                glyph.addClass("fa-check-circle")
                set_paste_buffer_to_text(text)
                /* select_element_text(event.target) */
            })
        })
    }

    let copy_and_edit_selectors = []

    if (page_format == "asciidoc")
        copy_and_edit_selectors = [".copy-and-edit .content code"]
    else
        copy_and_edit_selectors = ["code.language-copy-and-edit"]

    for (let selector of copy_and_edit_selectors) {
        $(selector).each((_, element) => {
            let parent = $(element).parent()
            let glyph = $("<span class='magic-code-block-glyph fas fa-user-edit' aria-hidden='true'></span>")
            parent.prepend(glyph)
            parent.click((event) => {
                let text = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                glyph.removeClass("fa-user-edit")
                glyph.addClass("fa-check-circle")
                set_paste_buffer_to_text(text)
                /* select_element_text(event.target) */
            })
        })
    }

    // Register handlers for dashboard actions.

    register_action(
        "dashboard:expose-dashboard",
        "play",
        (args) => {
            return `Dashboard: Expose dashboard "${args.name}"`
        },
        "",
        (args, done, fail) => {
            if (dashboard) {
                expose_dashboard(args.name.toLowerCase())
                done()
            }
            else
                fail("Dashboard is not available")
        }
    )

    // Register handlers for terminal actions.

    register_action(
        "terminal:execute",
        "running",
        (args) => {
            let session = args.session || "1"
            return `Terminal: Execute command in terminal ${session}`
        },
        (args) => {
            return args.command
        },
        (args, done, fail) => {
            expose_dashboard("terminal")
            if (terminals) {
                execute_in_terminal(args.command, args.session || "1")
                done()
            }
            else
                fail("Terminals are not available")
        }
    )

    register_action(
        "terminal:execute-all",
        "running",
        (args) => {
            return `Terminal: Execute command in all terminals`
        },
        (args) => {
            return args.command
        },
        (args, done, fail) => {
            expose_dashboard("terminal")
            if (terminals) {
                execute_in_all_terminals(args.command)
                done()
            }
            else
                fail("Terminals are not available")
        }
    )

    register_action(
        "terminal:clear-all",
        "running",
        (args) => {
            return `Terminal: Clear all terminals (clear)`
        },
        "",
        (args, done, fail) => {
            expose_dashboard("terminal")
            if (terminals) {
                execute_in_all_terminals("clear")
                done()
            }
            else
                fail("Terminals are not available")
        }
    )

    register_action(
        "terminal:interrupt",
        "running",
        (args) => {
            let session = args.session || "1"
            return `Terminal: Interrupt command in terminal ${session}`
        },
        "<ctrl+c>",
        (args, done, fail) => {
            expose_dashboard("terminal")
            if (terminals) {
                execute_in_terminal("<ctrl+c>", args.session || "1")
                done()
            }
            else
                fail("Terminals are not available")
        }
    )

    register_action(
        "terminal:interrupt-all",
        "running",
        (args) => {
            return `Terminal: Interrupt commands in all terminals`
        },
        "<ctrl+c>",
        (args, done, fail) => {
            expose_dashboard("terminal")
            if (terminals) {
                execute_in_all_terminals("<ctrl+c>")
                done()
            }
            else
                fail("Terminals are not available")
        }
    )

    register_action(
        "terminal:input",
        "running",
        (args) => {
            let session = args.session || "1"
            return `Terminal: Input text in terminal ${session}`
        },
        (args) => {
            return args.text
        },
        (args, done, fail) => {
            expose_dashboard("terminal")
            if (terminals) {
                execute_in_terminal(args.text, args.session || "1")
                done()
            }
            else
                fail("Terminals are not available")
        }
    )

    // Register handlers for copy actions.

    register_action(
        "workshop:copy",
        "copy",
        (args) => {
            let session = args.session || "1"
            return `Workshop: Copy text to paste buffer`
        },
        (args) => {
            return args.text
        },
        (args, done, fail) => {
            set_paste_buffer_to_text(args.text)
            done()
        }
    )

    register_action(
        "workshop:copy-and-edit",
        "user-edit",
        (args) => {
            let session = args.session || "1"
            return `Workshop: Copy text to paste buffer, change values before use`
        },
        (args) => {
            return args.text
        },
        (args, done, fail) => {
            set_paste_buffer_to_text(args.text)
            done()
        }
    )

    // Register handlers for URL actions.

    register_action(
        "workshop:open-url",
        "external-link-alt",
        (args) => {
            return "Workshop: Open URL in browser"
        },
        (args) => {
            return args.url
        },
        (args, done, fail) => {
            window.open(args.url, "_blank")
            done()
        }
    )

    // Register handlers for code editor actions.

    register_action(
        "editor:open-file",
        "edit",
        (args) => {
            if (args.line)
                return `Editor: Open file "${args.file}" at line ${args.line}`
            return `Editor: Open file "${args.file}"`
        },
        "",
        (args, done, fail) => {
            expose_dashboard("editor")
            editor.open_file(args.file, args.line || 1, done, fail)
        }
    )

    register_action(
        "editor:append-lines-to-file",
        "file-import",
        (args) => {
            return `Editor: Append lines to file "${args.file}"`
        },
        (args) => {
            return args.value
        },
        (args, done, fail) => {
            expose_dashboard("editor")
            editor.append_lines_to_file(args.file, args.value || "", done, fail)
        }
    )

    register_action(
        "editor:insert-lines-before-line",
        "file-import",
        (args) => {
            return `Editor: Insert lines before line ${args.line} in file "${args.file}"`
        },
        (args) => {
            return args.value
        },
        (args, done, fail) => {
            expose_dashboard("editor")
            editor.insert_lines_before_line(args.file, args.line || "", args.value || "", done, fail)
        }
    )

    register_action(
        "editor:append-lines-after-text",
        "file-import",
        (args) => {
            return `Editor: Append lines after text "${args.text}" in file "${args.file}"`
        },
        (args) => {
            return args.value
        },
        (args, done, fail) => {
            expose_dashboard("editor")
            editor.append_lines_after_text(args.file, args.text || "", args.value || "", done, fail)
        }
    )

    register_action(
        "editor:insert-value-into-yaml",
        "file-import",
        (args) => {
            return `Editor: Insert value into YAML file "${args.file}" at "${args.path}"`
        },
        (args) => {
            return yaml.safeDump(args.value)
        },
        (args, done, fail) => {
            expose_dashboard("editor")
            editor.insert_value_into_yaml(args.file, args.path, args.value, done, fail)
        }
    )

    register_action(
        "editor:execute-command",
        "play",
        (args) => {
            return `Editor: Execute command "${args.command}"`
        },
        (args) => {
            if (!args.args)
                return ""
            return yaml.safeDump(args.args)
        },
        (args, done, fail) => {
            expose_dashboard("editor")
            editor.execute_command(args.command, args.args || [], done, fail)
        }
    )

    // Inject Google Analytics into the page if a tracking ID is provided.

    if ($body.data("google-tracking-id")) {
        gtag("set", {
            "custom_map": {
                "dimension1": "workshop_name",
                "dimension2": "session_namespace",
                "dimension3": "workshop_namespace",
                "dimension4": "training_portal",
                "dimension5": "ingress_domain",
                "dimension6": "ingress_protocol"
            }
        })

        gtag("config", $body.data("google-tracking-id"), {
            "workshop_name": $body.data("workshop-name"),
            "session_namespace": $body.data("session-namespace"),
            "workshop_namespace": $body.data("workshop-namespace"),
            "training_portal": $body.data("training-portal"),
            "ingress_domain": $body.data("ingress-domain"),
            "ingress_protocol": $body.data("ingress-portal")
        })

        if (!$body.data("prev-page")) {
            gtag("event", "Workshop/First", {
                "event_category": "workshop_name",
                "event_label": $body.data("workshop-name")
            })

            gtag("event", "Workshop/First", {
                "event_category": "session_namespace",
                "event_label": $body.data("session-namespace")
            })

            gtag("event", "Workshop/First", {
                "event_category": "workshop_namespace",
                "event_label": $body.data("workshop-namespace")
            })

            gtag("event", "Workshop/First", {
                "event_category": "training_portal",
                "event_label": $body.data("training-portal")
            })

            gtag("event", "Workshop/First", {
                "event_category": "ingress_domain",
                "event_label": $body.data("ingress-domain")
            })
        }

        gtag("event", "Workshop/View", {
            "event_category": "workshop_name",
            "event_label": $body.data("workshop-name")
        })

        gtag("event", "Workshop/View", {
            "event_category": "session_namespace",
            "event_label": $body.data("session-namespace")
        })

        gtag("event", "Workshop/View", {
            "event_category": "workshop_namespace",
            "event_label": $body.data("workshop-namespace")
        })

        gtag("event", "Workshop/View", {
            "event_category": "training_portal",
            "event_label": $body.data("training-portal")
        })

        gtag("event", "Workshop/View", {
            "event_category": "ingress_domain",
            "event_label": $body.data("ingress-domain")
        })

        if (!$body.data("next-page")) {
            gtag("event", "Workshop/Last", {
                "event_category": "workshop_name",
                "event_label": $body.data("workshop-name")
            })

            gtag("event", "Workshop/Last", {
                "event_category": "session_namespace",
                "event_label": $body.data("session-namespace")
            })

            gtag("event", "Workshop/Last", {
                "event_category": "workshop_namespace",
                "event_label": $body.data("workshop-namespace")
            })

            gtag("event", "Workshop/Last", {
                "event_category": "training_portal",
                "event_label": $body.data("training-portal")
            })

            gtag("event", "Workshop/Last", {
                "event_category": "ingress_domain",
                "event_label": $body.data("ingress-domain")
            })
        }
    }
})
