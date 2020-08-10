import * as path from "path"
import * as yaml from "js-yaml"
import * as $ from "jquery"
import "bootstrap"

declare var gtag: Function

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

let terminals: Terminals
let dashboard: Dashboard

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

$(document).ready(() => {
    if (parent) {
        if ((<any>parent).eduk8s) {
            terminals = (<any>parent).eduk8s.terminals
            dashboard = (<any>parent).eduk8s.dashboard
        }
    }

    // Inject Google Analytics into the page if a tracking ID is provided.

    let $body = $("body")

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

    let markdown_mapping = [
        ["code.language-execute", ""],
        ["code.language-execute-1", "1"],
        ["code.language-execute-2", "2"],
        ["code.language-execute-3", "3"],
        ["code.language-execute-all", "*"]
    ]

    if (terminals) {
        for (let [selector, id] of markdown_mapping) {
            $(selector).each((_, element) => {
                let parent = $(element).parent()
                let glyph = $(`<span class='magic-code-block-glyph fas fa-running' aria-hidden='true'><sup><sup>${id}</sup></sup></span>`)
                parent.prepend(glyph)
                parent.click((event) => {
                    let command = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                    if (event.shiftKey) {
                        glyph.removeClass("text-danger")
                        glyph.addClass("text-success")
                        set_paste_buffer_to_text(command)
                    }
                    else {
                        glyph.removeClass("text-success")
                        glyph.addClass("text-danger")
                        execute_in_terminal(command, id)
                    }
                    select_element_text(event.target)
                })
            })
        }
    }
    else {
        for (let [selector, id] of markdown_mapping) {
            $(selector).each((_, element) => {
                let parent = $(element).parent()
                let glyph = $("<span class='magic-code-block-glyph fas fa-copy' aria-hidden='true'></span>")
                parent.prepend(glyph)
                parent.click((event) => {
                    let command = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                    glyph.addClass("text-success")
                    set_paste_buffer_to_text(command)
                    select_element_text(event.target)
                })
            })
        }
    }

    $("code.language-copy").each((_, element) => {
        let parent = $(element).parent()
        let glyph = $("<span class='magic-code-block-glyph fas fa-copy' aria-hidden='true'></span>")
        parent.prepend(glyph)
        parent.click((event) => {
            let text = parent.contents().not($(".magic-code-block-glyph")).text().trim()
            glyph.addClass("text-success")
            set_paste_buffer_to_text(text)
            select_element_text(event.target)
        })
    })

    $("code.language-copy-and-edit").each((_, element) => {
        let parent = $(element).parent()
        let glyph = $("<span class='magic-code-block-glyph fas fa-user-edit' aria-hidden='true'></span>")
        parent.prepend(glyph)
        parent.click((event) => {
            let text = parent.contents().not($(".magic-code-block-glyph")).text().trim()
            glyph.addClass("text-success")
            set_paste_buffer_to_text(text)
            select_element_text(event.target)
        })
    })

    let asciidoc_mapping = [
        [".execute .content", ""],
        [".execute-1 .content", "1"],
        [".execute-2 .content", "2"],
        [".execute-3 .content", "3"],
        [".execute-all .content", "*"]
    ]

    if (terminals) {
        for (let [selector, id] of asciidoc_mapping) {
            $(selector).each((_, element) => {
                let parent = $(element).parent()
                let glyph = $(`<span class='magic-code-block-glyph fas fa-running' aria-hidden='true'><sup><sup>${id}</sup></sup></span>`)
                $(element).find(".highlight").prepend(glyph)
                parent.click((event) => {
                    if (event.shiftKey) {
                        let command = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                        glyph.removeClass("text-danger")
                        glyph.addClass("text-success")
                        set_paste_buffer_to_text(command)
                    }
                    else {
                        let command = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                        glyph.removeClass("text-success")
                        glyph.addClass("text-danger")
                        execute_in_terminal(command, id)
                    }
                    select_element_text(event.target)
                })
            })
        }
    }
    else {
        for (let [selector, id] of asciidoc_mapping) {
            $(selector).each((_, element) => {
                let parent = $(element).parent()
                let glyph = $("<span class='magic-code-block-glyph fas fa-copy' aria-hidden='true'></span>")
                $(element).find(".highlight").prepend(glyph)
                parent.click((event) => {
                    let command = parent.contents().not($(".magic-code-block-glyph")).text().trim()
                    glyph.addClass("text-success")
                    set_paste_buffer_to_text(command)
                    select_element_text(event.target)
                })
            })
        }
    }

    $(".copy .content").each((_, element) => {
        let parent = $(element).parent()
        let glyph = $("<span class='magic-code-block-glyph fas fa-copy' aria-hidden='true'></span>")
        $(element).find(".highlight").prepend(glyph)
        parent.click((event) => {
            let text = parent.contents().not($(".magic-code-block-glyph")).text().trim()
            glyph.addClass("text-success")
            set_paste_buffer_to_text(text)
            select_element_text(event.target)
        })
    })

    $(".copy-and-edit .content").each((_, element) => {
        let parent = $(element).parent()
        let glyph = $("<span class='magic-code-block-glyph fas fa-user-edit' aria-hidden='true'></span>")
        $(element).find(".highlight").prepend(glyph)
        parent.click((event) => {
            let text = parent.contents().not($(".magic-code-block-glyph")).text().trim()
            glyph.addClass("text-warning")
            set_paste_buffer_to_text(text)
            select_element_text(event.target)
        })
    })

    // Add markup and click handlers to code editor commands.

    function copy_args_from_element(element) {
        return yaml.load($(element).text().trim())
    }

    $("code.language-editor-open-file").each((_, element) => {
        let parent = $(element).parent()
        let title = $("<div class='magic-code-block-title'></div>").text("Editor: Open file")
        parent.before(title)
        let glyph = $("<span class='magic-code-block-glyph fas fa-edit' aria-hidden='true'></span>")
        parent.prepend(glyph)
        parent.click(function (event) {
            let args = copy_args_from_element(element)
            console.log('ARGS', args)
            glyph.addClass("text-success")
        })
    })

    $("code.language-editor-append-to-file").each((_, element) => {
        let parent = $(element).parent()
        let title = $("<div class='magic-code-block-title'></div>").text("Editor: Append to file")
        parent.before(title)
        let glyph = $("<span class='magic-code-block-glyph fas fa-file-import' aria-hidden='true'></span>")
        parent.prepend(glyph)
        parent.click(function (event) {
            let args = copy_args_from_element(element)
            console.log('ARGS', args)
            glyph.addClass("text-success")
        })
    })

    $("code.language-editor-insert-at-line").each((_, element) => {
        let parent = $(element).parent()
        let title = $("<div class='magic-code-block-title'></div>").text("Editor: Insert at line")
        parent.before(title)
        let glyph = $("<span class='magic-code-block-glyph fas fa-file-import' aria-hidden='true'></span>")
        parent.prepend(glyph)
        parent.click(function (event) {
            let args = copy_args_from_element(element)
            console.log('ARGS', args)
            glyph.addClass("text-success")
        })
    })

    $("code.language-editor-insert-before-text").each((_, element) => {
        let parent = $(element).parent()
        let title = $("<div class='magic-code-block-title'></div>").text("Editor: Insert before text")
        parent.before(title)
        let glyph = $("<span class='magic-code-block-glyph fas fa-file-import' aria-hidden='true'></span>")
        parent.prepend(glyph)
        parent.click(function (event) {
            let args = copy_args_from_element(element)
            console.log('ARGS', args)
            glyph.addClass("text-success")
        })
    })

    $("code.language-editor-insert-in-yaml").each((_, element) => {
        let parent = $(element).parent()
        let title = $("<div class='magic-code-block-title'></div>").text("Editor: Insert in yaml")
        parent.before(title)
        let glyph = $("<span class='magic-code-block-glyph fas fa-file-import' aria-hidden='true'></span>")
        parent.prepend(glyph)
        parent.click(function (event) {
            let args = copy_args_from_element(element)
            console.log('ARGS', args)
            glyph.addClass("text-success")
        })
    })

    $("code.language-editor-execute-command").each((_, element) => {
        let parent = $(element).parent()
        let title = $("<div class='magic-code-block-title'></div>").text("Editor: Execute command")
        parent.before(title)
        let glyph = $("<span class='magic-code-block-glyph fas fa-play' aria-hidden='true'></span>")
        parent.prepend(glyph)
        parent.click(function (event) {
            let args = copy_args_from_element(element)
            console.log('ARGS', args)
            glyph.addClass("text-success")
        })
    })
})
