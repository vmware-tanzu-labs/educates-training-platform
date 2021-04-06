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

function send_analytics_event(event: string, data = {}) {
    let payload = {
        event: {
            name: event,
            data: data
        }
    }

    $.ajax({
        type: "POST",
        url: "/session/event",
        contentType: "application/json",
        data: JSON.stringify(payload),
        dataType: "json",
        success: () => { },
        error: e => { console.error("Unable to report analytics event:", e) }
    })
}

interface Terminals {
    execute_in_terminal(command: string, id: string): void
    execute_in_all_terminals(command: string): void
    reload_terminals(): void
}

interface Dashboard {
    expose_terminal(name: string): boolean
    expose_dashboard(name: string): boolean
    create_dashboard(name: string, url: string): boolean
    delete_dashboard(name: string): boolean
    reload_dashboard(name: string, url?: string): boolean
    collapse_workshop(): void
    reload_workshop(): void
    finished_workshop(): void
    preview_image(src: string, title: string): void
}

function parent_terminals(): Terminals {
    if (parent && (<any>parent).eduk8s)
        return (<any>parent).eduk8s.terminals
}

function parent_dashboard(): Dashboard {
    if (parent && (<any>parent).eduk8s)
        return (<any>parent).eduk8s.dashboard
}

class Editor {
    readonly retries = 25
    readonly retry_delay = 1000

    private url: string = null

    constructor() {
        let $body = $("body")

        let session_namespace = $body.data('session-namespace')
        let ingress_domain = $body.data('ingress-domain')
        let ingress_protocol = $body.data('ingress-protocol')
        let ingress_port_suffix = $body.data('ingress-port-suffix')

        if (session_namespace && ingress_domain && ingress_protocol)
            this.url = `${ingress_protocol}://${session_namespace}.${ingress_domain}${ingress_port_suffix}/code-server`
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

    select_matching_text(file: string, text: string, isRegex: boolean, before: number, after: number, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        if (!text)
            return fail("No text to match provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, text, isRegex, before, after })
        this.execute_call("/editor/select-matching-text", data, done, fail)
    }

    append_lines_to_file(file: string, text: string, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, paste: text })
        this.execute_call("/editor/paste", data, done, fail)
    }

    insert_lines_before_line(file: string, line: number, text: string, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, line, paste: text })
        this.execute_call("/editor/paste", data, done, fail)
    }

    append_lines_after_match(file: string, match: string, text: string, done, fail) {
        if (!this.url)
            return fail("Editor not available")

        if (!file)
            return fail("No file name provided")

        if (!match)
            return fail("No string to match provided")

        file = this.fixup_path(file)
        let data = JSON.stringify({ file, prefix: match, paste: text })
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

export let editor: Editor

export function execute_in_terminal(command: string, id: string, done = () => { }, fail = (_) => { }) {
    let terminals = parent_terminals()

    if (!terminals)
        return fail("Terminals are not available")

    id = id || "1"

    if (id == "*") {
        expose_dashboard("terminal")
        terminals.execute_in_all_terminals(command)
    }
    else {
        expose_terminal(id)
        terminals.execute_in_terminal(command, id)
    }

    done()
}

export function execute_in_all_terminals(command: string, done = () => { }, fail = (_) => { }) {
    let terminals = parent_terminals()

    if (!terminals)
        return fail("Terminals are not available")

    expose_dashboard("terminal")

    terminals.execute_in_all_terminals(command)

    done()
}

export function reload_terminals(done = () => { }, fail = (_) => { }) {
    let terminals = parent_terminals()

    if (!terminals)
        return fail("Terminals are not available")

    expose_dashboard("terminal")

    terminals.reload_terminals()

    done()
}

export function expose_terminal(name: string, done = () => { }, fail = (_) => { }) {
    let dashboard = parent_dashboard()

    if (!dashboard)
        return fail("Dashboard is not available")

    if (!dashboard.expose_terminal(name))
        return fail("Terminal does not exist")

    done()
}

export function expose_dashboard(name: string, done = () => { }, fail = (_) => { }) {
    let dashboard = parent_dashboard()

    if (!dashboard)
        return fail("Dashboard is not available")

    if (!dashboard.expose_dashboard(name))
        return fail("Dashboard does not exist")

    done()
}

export function create_dashboard(name: string, url: string, done = () => { }, fail = (_) => { }) {
    let dashboard = parent_dashboard()

    if (!dashboard)
        return fail("Dashboard is not available")

    if (!dashboard.create_dashboard(name, url))
        return fail("Dashboard already exists")

    done()
}

export function delete_dashboard(name: string, done = () => { }, fail = (_) => { }) {
    let dashboard = parent_dashboard()

    if (!dashboard)
        return fail("Dashboard is not available")

    if (!dashboard.delete_dashboard(name))
        return fail("Dashboard does not exist")

    done()
}

export function reload_dashboard(name: string, url: string, done = () => { }, fail = (_) => { }) {
    let dashboard = parent_dashboard()

    if (!dashboard) {
        fail("Dashboard is not available")
        return
    }

    if (!dashboard.reload_dashboard(name, url))
        return fail("Dashboard does not exist")

    done()
}

export function collapse_workshop(done = () => { }, fail = (_) => { }) {
    let dashboard = parent_dashboard()

    if (!dashboard)
        return fail("Dashboard is not available")

    dashboard.collapse_workshop()

    done()
}

export function reload_workshop(done = () => { }, fail = (_) => { }) {
    let dashboard = parent_dashboard()

    if (!dashboard)
        return fail("Dashboard is not available")

    dashboard.reload_workshop()

    done()
}

export function finished_workshop() {
    let dashboard = parent_dashboard()

    if (dashboard)
        dashboard.finished_workshop()
}

function preview_image(src: string, title: string) {
    let dashboard = parent_dashboard()

    if (!dashboard) {
        $("#preview-image-element").attr("src", src)
        $("#preview-image-title").text(title)
        $("#preview-image-dialog").modal("show")
    }
    else
        dashboard.preview_image(src, title)
}

function execute_examiner_test(name, args, timeout, retries, delay, cascade, done, fail) {
    if (!name)
        return fail("Test name not provided")

    let data = JSON.stringify({ args, timeout })

    let url = `/examiner/test/${name}`

    function attempt_call() {
        $.ajax({
            type: 'POST',
            url: url,
            data: data,
            contentType: "application/json",
            dataType: "json"
        })
            .done((result) => {
                if (!result["success"]) {
                    if (retries--)
                        setTimeout(attempt_call, delay * 1000)
                    else
                        fail(result["message"] || "Invalid response")
                }
                else {
                    done()
                }
            })
            .fail((error) => {
                fail("Unexpected HTTP error")
            })
    }

    attempt_call()
}

export function register_action(options: any) {
    let defaults = {
        name: undefined,
        glyph: "fa-bug",
        args: undefined,
        title: "Action: Invalid action definition",
        body: undefined,
        handler: (args, done, fail) => { fail("Invalid action definition") },
        waiting: undefined,
        spinner: false,
        success: undefined,
        failure: "bg-danger",
        setup: (args, element) => { },
        trigger: (args, element) => { },
        finish: (args, element, error) => { },
        cooldown: 1,
    }

    options = { ...defaults, ...options }

    let name: string = options["name"]
    let glyph: string = options["glyph"]
    let args: any = options["args"]
    let title: any = options["title"]
    let body: any = options["body"]
    let handler: any = options["handler"]
    let waiting: string = options["waiting"]
    let spinner: boolean = options["spinner"]
    let success: string = options["success"]
    let failure: string = options["failure"]
    let setup: any = options["setup"]
    let trigger: any = options["trigger"]
    let finish: any = options["finish"]
    let cooldown: number = options["cooldown"]

    if (name === undefined)
        return

    let classname = name.replace(":", "\\:")

    let selectors = []

    if ($("body").data("page-format") == "asciidoc")
        selectors = [`.${classname} .content code`]
    else
        selectors = [`code.language-${classname}`]

    let index = 1

    for (let selector of selectors) {
        $(selector).each((_, element) => {
            let code_element = $(element)
            let parent_element = code_element.parent()

            code_element.addClass("magic-code-block")
            parent_element.addClass("magic-code-block-parent")

            // Must be set as attr() and not data() so we can use a selector
            // in jquery based on data attribute later on. This is because
            // data() doesn't store it on the HTML element but separate.

            parent_element.attr("data-action-name", name)
            parent_element.attr("data-action-index", `${index}`)

            index++

            let action_args = code_element.text()

            if (args === "json") {
                action_args = JSON.parse(action_args.trim() || "{}")
            }
            else if (args === "yaml") {
                action_args = yaml.load(action_args.trim() || "{}")
            }
            else if (typeof args === "function") {
                action_args = args(action_args)
            }

            let title_string = title

            if (typeof title === "function")
                title_string = title(action_args)

            let title_element = $("<div class='magic-code-block-title'></div>").text(title_string)
            let glyph_element = $(`<span class='magic-code-block-glyph fas ${glyph}' aria-hidden='true'></span>`)

            parent_element.before(title_element)
            title_element.prepend(glyph_element)

            let body_string = body

            if (typeof body === "function")
                body_string = body(action_args)

            if (typeof body_string !== "string")
                body_string = ""

            code_element.text(body_string)

            $.each([title_element, parent_element], (_, target) => {
                target.on("click", (event) => {
                    if (!event.shiftKey) {
                        console.log(`[${title_string}] Execute:`, action_args)

                        let triggered = $(parent_element).data("triggered")
                        let completed = $(parent_element).data("completed")

                        let now = new Date().getTime()

                        if (cooldown) {
                            if (triggered && !completed) {
                                console.log(`[${title_string}] Cooldown: Executing`)

                                return
                            }

                            if (completed) {
                                if (((now - completed) / 1000) < cooldown) {
                                    console.log(`[${title_string}] Cooldown: Interval`)
                                    return
                                }
                            }
                        }

                        $(parent_element).data("triggered", now)
                        $(parent_element).data("completed", undefined)

                        if (success)
                            title_element.removeClass(`${success}`)
                        if (failure)
                            title_element.removeClass(`${failure}`)

                        if (waiting) {
                            glyph_element.removeClass(`${glyph}`)
                            glyph_element.addClass(`${waiting}`)
                            if (spinner)
                                glyph_element.addClass("fa-spin")
                        }

                        trigger(action_args, parent_element)

                        handler(action_args, () => {
                            console.log(`[${title_string}] Success`)

                            let now = new Date().getTime()

                            $(parent_element).data("completed", now)

                            if (success)
                                title_element.addClass(`${success}`)
                            if (failure)
                                title_element.removeClass(`${failure}`)

                            glyph_element.removeClass(`${glyph}`)

                            if (waiting) {
                                glyph_element.removeClass(`${waiting}`)
                                glyph_element.removeClass("fa-spin")
                            }

                            glyph_element.addClass("fa-check-circle")

                            finish(action_args, parent_element)
                        }, (error) => {
                            console.log(`[${title_string}] Failure: ${error}`)

                            let now = new Date().getTime()

                            $(parent_element).data("completed", now)

                            if (failure)
                                title_element.addClass(`${failure}`)
                            if (success)
                                title_element.removeClass(`${success}`)

                            glyph_element.addClass(`${glyph}`)

                            if (waiting) {
                                glyph_element.removeClass(`${waiting}`)
                                glyph_element.removeClass("fa-spin")
                            }

                            finish(action_args, parent_element, error)
                        })
                    }
                    else {
                        event.preventDefault()
                        event.stopPropagation()
                        set_paste_buffer_to_text(body_string)
                    }

                    window.getSelection().removeAllRanges()
                })
            })

            setup(action_args, parent_element)
        })
    }
}

$(document).ready(() => {
    editor = new Editor()

    let $body = $("body")

    let page_format = $body.data("page-format")

    // Set up page navigation buttons in header and at bottom of pages.

    $("button[data-goto-page]").each((_, element) => {
        if ($(element).data("goto-page")) {
            $(element).removeAttr("disabled")
            $(element).on("click", () => {
                location.href = path.join("/workshop/content", $(element).data("goto-page"))
            })
        }
        else {
            $(element).removeClass("fa-inverse")
        }
    })

    $("#next-page").on("click", (event) => {
        let next_page = $(event.target).data("next-page")
        let exit_link = $(event.target).data("exit-link")
        let restart_url = $(event.target).data("restart-url")

        let dashboard = parent_dashboard()

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
        $(element).on("click", () => {
            preview_image(image.src, image.alt)
        })
    })

    // Register handlers for terminal actions.

    register_action({
        name: "execute",
        glyph: "fa-running",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Terminal"
            let subject = args.title || "Execute command in terminal \"1\""
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args
        },
        handler: (args, done, fail) => {
            execute_in_terminal(args.trim(), "1", done, fail)
        }
    })

    register_action({
        name: "execute-1",
        glyph: "fa-running",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Terminal"
            let subject = args.title || "Execute command in terminal \"1\""
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args
        },
        handler: (args, done, fail) => {
            execute_in_terminal(args.trim(), "1", done, fail)
        }
    })

    register_action({
        name: "execute-2",
        glyph: "fa-running",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Terminal"
            let subject = args.title || "Execute command in terminal \"2\""
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args
        },
        handler: (args, done, fail) => {
            execute_in_terminal(args.trim(), "2", done, fail)
        }
    })

    register_action({
        name: "execute-3",
        glyph: "fa-running",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Terminal"
            let subject = args.title || "Execute command in terminal \"3\""
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args
        },
        handler: (args, done, fail) => {
            execute_in_terminal(args.trim(), "3", done, fail)
        }
    })

    register_action({
        name: "execute-all",
        glyph: "fa-running",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Terminal"
            let subject = args.title || "Execute command in all terminals"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args
        },
        handler: (args, done, fail) => {
            execute_in_all_terminals(args.trim(), done, fail)
        }
    })

    register_action({
        name: "terminal:execute",
        glyph: "fa-running",
        args: "yaml",
        title: (args) => {
            let session = args.session || "1"
            let prefix = args.prefix || "Terminal"
            let subject = args.title || `Execute command in terminal "${session}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.command
        },
        handler: (args, done, fail) => {
            execute_in_terminal(args.command, args.session || "1", done, fail)
        }
    })

    register_action({
        name: "terminal:execute-all",
        glyph: "fa-running",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Terminal"
            let subject = args.title || "Execute command in all terminals"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.command
        },
        handler: (args, done, fail) => {
            execute_in_all_terminals(args.command, done, fail)
        }
    })

    register_action({
        name: "terminal:clear-all",
        glyph: "fa-running",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Terminal"
            let subject = args.title || "Clear all terminals"
            return `${prefix}: ${subject}`
        },
        body: "clear",
        handler: (args, done, fail) => {
            execute_in_all_terminals("clear", done, fail)
        }
    })

    register_action({
        name: "terminal:interrupt",
        glyph: "fa-running",
        args: "yaml",
        title: (args) => {
            let session = args.session || "1"
            let prefix = args.prefix || "Terminal"
            let subject = args.title || `Interrupt command in terminal "${session}"`
            return `${prefix}: ${subject}`
        },
        body: "<ctrl+c>",
        handler: (args, done, fail) => {
            execute_in_terminal("<ctrl+c>", args.session || "1", done, fail)
        }
    })

    register_action({
        name: "terminal:interrupt-all",
        glyph: "fa-running",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Terminal"
            let subject = args.title || "Interrupt commands in all terminals"
            return `${prefix}: ${subject}`
        },
        body: "<ctrl+c>",
        handler: (args, done, fail) => {
            execute_in_all_terminals("<ctrl+c>", done, fail)
        }
    })

    register_action({
        name: "terminal:input",
        glyph: "fa-running",
        args: "yaml",
        title: (args) => {
            let session = args.session || "1"
            let prefix = args.prefix || "Terminal"
            let subject = args.title || `Input text in terminal "${session}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.text
        },
        handler: (args, done, fail) => {
            execute_in_terminal(args.text, args.session || "1", done, fail)
        }
    })

    // Register handlers for copy actions.

    register_action({
        name: "copy",
        glyph: "fa-copy",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Workshop"
            let subject = args.title || "Copy text to paste buffer"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args
        },
        handler: (args, done, fail) => {
            set_paste_buffer_to_text(args.trim())
            done()
        },
        cooldown: 0
    })

    register_action({
        name: "copy-and-edit",
        glyph: "fa-user-edit",
        args: "text",
        title: (args) => {
            let prefix = args.prefix || "Workshop"
            let subject = args.title || "Copy text to paste buffer, change values before use"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args
        },
        handler: (args, done, fail) => {
            set_paste_buffer_to_text(args.trim())
            done()
        },
        cooldown: 0
    })

    register_action({
        name: "workshop:copy",
        glyph: "fa-copy",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Workshop"
            let subject = args.title || "Copy text to paste buffer"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.text
        },
        handler: (args, done, fail) => {
            set_paste_buffer_to_text(args.text)
            done()
        },
        cooldown: 0
    })

    register_action({
        name: "workshop:copy-and-edit",
        glyph: "fa-user-edit",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Workshop"
            let subject = args.title || "Copy text to paste buffer, change values before use"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.text
        },
        handler: (args, done, fail) => {
            set_paste_buffer_to_text(args.text)
            done()
        },
        cooldown: 0
    })

    // Register handlers for dashboard and URL actions.

    register_action({
        name: "dashboard:expose-dashboard",
        glyph: "fa-play",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Dashboard"
            let subject = args.title || `Expose dashboard "${args.name}"`
            return `${prefix}: ${subject}`
        },
        body: "",
        handler: (args, done, fail) => {
            expose_dashboard(args.name, done, fail)
        }
    })

    register_action({
        name: "dashboard:open-dashboard",
        glyph: "fa-eye",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Dashboard"
            let subject = args.title || `Open dashboard "${args.name}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return ""
        },
        handler: (args, done, fail) => {
            expose_dashboard(args.name, done, fail)
        }
    })

    register_action({
        name: "dashboard:create-dashboard",
        glyph: "fa-plus-circle",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Dashboard"
            let subject = args.title || `Create dashboard "${args.name}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.url
        },
        handler: (args, done, fail) => {
            create_dashboard(args.name, args.url, done, fail)
        }
    })

    register_action({
        name: "dashboard:delete-dashboard",
        glyph: "fa-trash-alt",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Dashboard"
            let subject = args.title || `Delete dashboard "${args.name}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return ""
        },
        handler: (args, done, fail) => {
            delete_dashboard(args.name, done, fail)
        }
    })

    register_action({
        name: "dashboard:reload-dashboard",
        glyph: "fa-sync-alt",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Dashboard"
            let subject = args.title || `Reload dashboard "${args.name}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.url
        },
        handler: (args, done, fail) => {
            reload_dashboard(args.name, args.url, done, fail)
        }
    })

    register_action({
        name: "dashboard:open-url",
        glyph: "fa-external-link-alt",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Dashboard"
            let subject = args.title || "Open URL in browser"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.url
        },
        handler: (args, done, fail) => {
            window.open(args.url, "_blank")
            done()
        },
        cooldown: 3
    })

    // Register handlers for code editor actions.

    register_action({
        name: "editor:open-file",
        glyph: "fa-edit",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Editor"
            let subject = args.title
            if (!args.title) {
                if (args.line)
                    subject = `Open file "${args.file}" at line ${args.line}`
                else
                    subject = `Open file "${args.file}"`
            }
            return `${prefix}: ${subject}`
        },
        body: "",
        handler: (args, done, fail) => {
            expose_dashboard("editor")
            editor.open_file(args.file, args.line || 1, done, fail)
        },
        waiting: "fa-cog",
        spinner: true,
        cooldown: 3
    })

    register_action({
        name: "editor:select-matching-text",
        glyph: "fa-search",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Editor"
            let subject = args.title || `Select text in file "${args.file}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.text
        },
        handler: (args, done, fail) => {
            expose_dashboard("editor")
            editor.select_matching_text(args.file, args.text, args.isRegex, args.before, args.after, done, fail)
        },
        waiting: "fa-cog",
        spinner: true,
        cooldown: 3
    })

    register_action({
        name: "editor:append-lines-to-file",
        glyph: "fa-file-import",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Editor"
            let subject = args.title || `Append lines to file "${args.file}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.text
        },
        handler: (args, done, fail) => {
            expose_dashboard("editor")
            editor.append_lines_to_file(args.file, args.text || "", done, fail)
        },
        waiting: "fa-cog",
        spinner: true,
        cooldown: 3
    })

    register_action({
        name: "editor:insert-lines-before-line",
        glyph: "fa-file-import",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Editor"
            let subject = args.title || `Insert lines before line ${args.line} in file "${args.file}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.text
        },
        handler: (args, done, fail) => {
            expose_dashboard("editor")
            editor.insert_lines_before_line(args.file, args.line || "", args.text || "", done, fail)
        },
        waiting: "fa-cog",
        spinner: true,
        cooldown: 3
    })

    register_action({
        name: "editor:append-lines-after-match",
        glyph: "fa-file-import",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Editor"
            let subject = args.title || `Append lines after "${args.match}" in file "${args.file}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.text
        },
        handler: (args, done, fail) => {
            expose_dashboard("editor")
            editor.append_lines_after_match(args.file, args.match || "", args.text || "", done, fail)
        },
        waiting: "fa-cog",
        spinner: true,
        cooldown: 3
    })

    register_action({
        name: "editor:insert-value-into-yaml",
        glyph: "fa-file-import",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Editor"
            let subject = args.title || `Insert value into YAML file "${args.file}" at "${args.path}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return yaml.safeDump(args.value)
        },
        handler: (args, done, fail) => {
            expose_dashboard("editor")
            editor.insert_value_into_yaml(args.file, args.path, args.value, done, fail)
        },
        waiting: "fa-cog",
        spinner: true,
        cooldown: 3
    })

    register_action({
        name: "editor:execute-command",
        glyph: "fa-play",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Editor"
            let subject = args.title || `Execute command "${args.command}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            if (!args.args)
                return ""
            return yaml.safeDump(args.args)
        },
        handler: (args, done, fail) => {
            expose_dashboard("editor")
            editor.execute_command(args.command, args.args || [], done, fail)
        },
        waiting: "fa-cog",
        spinner: true,
        cooldown: 3
    })

    // Register handlers for examiner actions.

    register_action({
        name: "examiner:execute-test",
        glyph: "fa-tasks",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Examiner"
            let subject = args.title || `Execute test case "${args.name}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return args.description || ""
        },
        handler: (args, done, fail) => {
            execute_examiner_test(
                args.name,
                args.args || [],
                args.timeout || 15,
                args.retries || 0,
                args.delay || 1,
                args.cascade || false,
                done,
                fail)
        },
        waiting: "fa-cog",
        spinner: true,
        setup: (args, element) => {
            if (args.autostart)
                element.attr("data-examiner-autostart", "true")
        },
        finish: (args, element, error) => {
            if (!args.cascade || error)
                return
            let name = element.data("action-name")
            let index = parseInt(element.data("action-index")) + 1
            $("pre").filter(`[data-action-name='${name}'][data-action-index='${index}']`).trigger("click")
        }
    })

    // Register handler for file download actions.

    register_action({
        name: "files:download-file",
        glyph: "fa-download",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Files"
            let subject = args.title || `Download file "${args.path}"`
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return ""
        },
        handler: (args, done, fail) => {
            let pathname = `/files/${args.path}`
            let basename = path.basename(pathname)
            let element = document.createElement("a")
            element.setAttribute("href", pathname)
            element.setAttribute("download", basename)
            element.style.display = "none"
            document.body.appendChild(element)
            element.click()
            document.body.removeChild(element)
            done()
        }
    })

    // Register handlers for section actions. These need to be done last.

    register_action({
        name: "section:heading",
        glyph: "fa-info-circle",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Section"
            let subject = args.title || "Instructions"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return ""
        },
        handler: (args, done, fail) => {
            done()
        },
    })

    register_action({
        name: "section:begin",
        glyph: "fa-chevron-down",
        args: "yaml",
        title: (args) => {
            let prefix = args.prefix || "Section"
            let subject = args.title || "Instructions"
            return `${prefix}: ${subject}`
        },
        body: (args) => {
            return ""
        },
        handler: (args, done, fail) => {
            done()
        },
        trigger: (args, element) => {
            let name = args.name || "*"
            let elements = element.nextUntil(`.magic-code-block-parent[data-action-name='section:end'][data-section-name='${name}']`).not(":last").filter(`[data-content-name='${name}']`)
            elements.show()
            elements.filter("[data-action-name='examiner:execute-test'][data-examiner-autostart]").trigger("click")
        },
        setup: (args, element) => {
            let name = args.name || "*"
            element.attr("data-section-name", name)
        }
    })

    register_action({
        name: "section:end",
        glyph: "fa-ban",
        args: "yaml",
        title: (args) => {
            return "Section: End"
        },
        body: (args) => {
            return ""
        },
        handler: (args, done, fail) => {
            fail()
        },
        setup: (args, element) => {
            let name = args.name || "*"
            element.attr("data-section-name", name)
            element.attr("data-content-name", name)
            let elements = element.prevUntil(`.magic-code-block-parent[data-action-name='section:begin'][data-section-name='${name}']`)
            let start = elements.last().prev()
            if (start.data("action-name") == "section:begin" && start.data("section-name") == name) {
                elements.not("[data-content-name]").attr("data-content-name", name)
                elements.hide()
                element.hide()
            }
        }
    })

    // Trigger autostart examiner actions at top level. 

    $("[data-examiner-autostart='true']").not("[data-content-name]").trigger("click")

    // Generate analytics event if a tracking ID is provided.

    send_analytics_event("Workshop/View", {
        prev: $body.data("prev-page"),
        current: $body.data("current-page"),
        next: $body.data("next-page"),
        step: $body.data("page-step"),
        total: $body.data("pages-total"),
    })

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

        let gsettings = {
            "workshop_name": $body.data("workshop-name"),
            "session_namespace": $body.data("session-namespace"),
            "workshop_namespace": $body.data("workshop-namespace"),
            "training_portal": $body.data("training-portal"),
            "ingress_domain": $body.data("ingress-domain"),
            "ingress_protocol": $body.data("ingress-portal")
        }

        if ($body.data("ingress-portal") == "https")
            gsettings["cookie_flags"] = "max-age=86400;secure;samesite=none"

        gtag("config", $body.data("google-tracking-id"), gsettings)

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
