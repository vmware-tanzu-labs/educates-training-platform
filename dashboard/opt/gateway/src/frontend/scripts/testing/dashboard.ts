import * as $ from "jquery"
let Split = require("split.js")
declare var eduk8s: any

$(document).ready(() => {
    let terminals: JQuery = $("#terminals")
    let dashboard: JQuery = $("#dashboard")

    if (dashboard) {
        Split(["#controls-pane", "#terminals-pane"], {
            gutterSize: 8,
            sizes: [20, 80],
            cursor: "row-resize",
            snapOffset: 120,
            minSize: 0,
        })
    }

    if (terminals) {
        Split(["#terminal-1", "#terminal-2"], {
            gutterSize: 8,
            sizes: [60, 40],
            direction: "vertical"
        })
    }

    $(".execute").click((event) => {
        let session_id = $(event.target).data("session-id")
        let input = $(event.target).data("input")
        eduk8s.terminals.execute_in_terminal(input, session_id)
    })

    $(".disconnect").click((event) => {
        let session_id = $(event.target).data("session-id")
        eduk8s.terminals.disconnect_terminal(session_id)
    })

    $(".reconnect").click((event) => {
        let session_id = $(event.target).data("session-id")
        eduk8s.terminals.reconnect_terminal(session_id)
    })
})