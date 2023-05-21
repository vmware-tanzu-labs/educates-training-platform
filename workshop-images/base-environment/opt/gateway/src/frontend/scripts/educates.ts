import * as $ from "jquery"
import * as url from "url"
import "bootstrap"

import { Terminal } from "xterm"
import { FitAddon } from "xterm-addon-fit"
import { WebLinksAddon } from "xterm-addon-web-links"

import { ResizeSensor } from "css-element-queries"

const FontFaceObserver = require("fontfaceobserver")

const _ = require("lodash")

const Split = require("split.js")

declare var gtag: Function
declare var clarity: Function

function string_to_slug(str: string) {
    str = str.trim()
    str = str.toLowerCase()

    return str
        .replace(/[^a-z0-9 -]/g, "") // remove invalid chars
        .replace(/\s+/g, "-") // collapse whitespace and replace by -
        .replace(/-+/g, "-") // collapse dashes
        .replace(/^-+/, "") // trim - from start of text
        .replace(/-+$/, "") // trim - from end of text
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

enum PacketType {
    HELLO,
    PING,
    DATA,
    RESIZE,
    EXIT,
    ERROR
}

interface Packet {
    type: PacketType
    id: string
    args?: any
}

interface HelloPacketArgs {
    token: string
    cols: number
    rows: number
    seq: number
}

interface InboundDataPacketArgs {
    data: string
    seq: number
}

interface OutboundDataPacketArgs {
    data: string
}

interface ResizePacketArgs {
    cols: number
    rows: number
}

interface ErrorPacketArgs {
    reason: string
}

interface BufferedDataBlock {
    text: string
    bracketed: boolean
}

class TerminalSession {
    private id: string
    private element: HTMLElement
    private endpoint: string
    private terminal: Terminal
    private fitter: FitAddon
    private sensor: ResizeSensor
    private socket: WebSocket
    private started: Date
    private sequence: number
    private blocked: boolean
    private buffer: BufferedDataBlock[]
    private reconnecting: boolean
    private reconnectTimer: any
    private shutdown: boolean

    constructor(context: string, id: string, element: HTMLElement, endpoint: string) {
        this.id = id

        // If a context is supplied, prefix the terminal session ID used for
        // the backend with the context. This means can have similarly named
        // terminal IDs used on frontend, but in different contexts on the
        // backend so they don't clash.

        if (context)
            this.id = `${context}:${id}`

        this.element = element
        this.endpoint = endpoint
        this.sequence = -1

        this.blocked = true
        this.buffer = []

        this.shutdown = false
        this.reconnecting = false

        this.terminal = new Terminal({
            cursorBlink: true,
            fontFamily: "SourceCodePro"
        })

        this.fitter = new FitAddon()
        this.terminal.loadAddon(this.fitter)

        this.terminal.loadAddon(new WebLinksAddon())

        // Ensure that the element the terminal is contained in is visible.
        // This is just to ensure that dimensions can be correctly calculated.

        let self = this

        function wait_until_visible() {
            if (!self.element.offsetParent)
                setTimeout(wait_until_visible, 300)
            else
                self.configure_session()
        }

        wait_until_visible()
    }

    private configure_session() {
        this.terminal.open(this.element)

        // We fit the window now. The size details will be sent with the
        // initial hello message sent to the terminal server.

        this.fitter.fit()

        let parsed_url = url.parse(window.location.origin)

        let protocol = parsed_url.protocol == "https:" ? "wss" : "ws"
        let host = parsed_url.host
        let pathname = "/terminal/server"

        let server_url = `${protocol}://${host}${pathname}`

        console.log("Configure session for terminal", this.id)

        this.socket = new WebSocket(server_url)

        this.configure_handlers()
        this.configure_sensors()

        // If there is more than one terminal session, if this is the first
        // session ensure it grabs focus. Does mean that if creating extra
        // sessions in separate window that they will not grab focus. Is
        // better than a secondary session grabbing focus when have more than
        // one on the page.

        if (this.id == "1")
            this.focus()
    }

    private configure_handlers() {
        if (this.shutdown)
            return

        console.log("Configure handlers for terminal", this.id)

        $(this.element).removeClass("notify-closed notify-exited")
        $(this.element).removeClass("notify-hijacked notify-forbidden")

        $("#refresh-button").removeClass("terminal-" + this.id + "-refresh-required")

        this.socket.onerror = (event) => {
            console.error("WebSocket error observed:", event)
        }

        let socket: WebSocket = this.socket

        this.socket.onopen = () => {
            // If the socket isn't the one currently associated with the
            // terminal then bail out straight away as some sort of mixup has
            // occurred. Close the socket for good measure.

            console.log("Connection opened to terminal", this.id)

            if (this.reconnectTimer) {
                console.log("Clear reconnection timeout for terminal", this.id)
                clearTimeout(this.reconnectTimer)
                this.reconnectTimer = null
            }

            if (socket !== this.socket) {
                console.warn("Multiple connections to terminal", this.id)
                socket.close()
                return
            }

            this.reconnecting = false

            this.started = new Date()

            // The sequence number indicates from where in the buffered data
            // kept by the server side, data should be returned on an initial
            // connection. This is to avoid replaying data we already have
            // previously received. Instead will only get what haven't seen
            // yet. If this is a completely new session, the sequence number
            // will start out as -1 so we will be sent everything.

            let args: HelloPacketArgs = {
                token: this.endpoint,
                cols: this.terminal.cols,
                rows: this.terminal.rows,
                seq: this.sequence
            }

            this.send_message(PacketType.HELLO, args)

            // A sequence number of -1 means this is a completely new session.
            // In this case we need to setup the callback for receiving input
            // data from the terminal and initiate the pings. We can only do
            // this once else we get duplicate registrations if we have to
            // reconnect because the connection is dropped.

            if (this.sequence == -1) {
                console.log("Connecting terminal", this.id)

                this.terminal.onData((data) => {
                    let args: OutboundDataPacketArgs = { data: data }
                    this.send_message(PacketType.DATA, args)
                })

                this.initiate_pings()

                // Set sequence number to 0 so we don't do this all again.

                this.sequence = 0

                // Schedule unblocking of output to remote session and flush
                // out anything which was buffered while waiting. It is
                // blocked initially to allow any terminal to be visible
                // and the remote shell or application to start and display
                // any initial prompt. If a reconnect occurs while we were
                // waiting, discard the data.

                setTimeout(async () => {
                    if (socket !== this.socket) {
                        this.buffer = []
                        return
                    }

                    this.blocked = false

                    let buffer = this.buffer
                    this.buffer = []

                    if (buffer.length) {
                        console.log("Flushing data to terminal", this.id)

                        for (let block of buffer)
                            await this.paste(block.text, block.bracketed)
                    }
                }, 1000)

                // Generate analytics event to track terminal connect.

                let $body = $("body")

                send_analytics_event("Terminal/Connect", { terminal: this.id })

                if ($body.data("google-tracking-id")) {
                    gtag("event", "Terminal/Connect", {
                        "event_category": "workshop_name",
                        "event_label": $body.data("workshop-name")
                    })

                    gtag("event", "Terminal/Connect", {
                        "event_category": "session_name",
                        "event_label": $body.data("session-namespace")
                    })

                    gtag("event", "Terminal/Connect", {
                        "event_category": "environment_name",
                        "event_label": $body.data("workshop-namespace")
                    })

                    gtag("event", "Terminal/Connect", {
                        "event_category": "training_portal",
                        "event_label": $body.data("training-portal")
                    })

                    gtag("event", "Terminal/Connect", {
                        "event_category": "ingress_domain",
                        "event_label": $body.data("ingress-domain")
                    })
                }
            }
            else {
                console.log("Re-connecting terminal", this.id)

                // Generate analytics event to track terminal reconnect.

                let $body = $("body")

                send_analytics_event("Terminal/Reconnect", { terminal: this.id })

                if ($body.data("google-tracking-id")) {
                    gtag("event", "Terminal/Reconnect", {
                        "event_category": "workshop_name",
                        "event_label": $body.data("workshop-name")
                    })

                    gtag("event", "Terminal/Reconnect", {
                        "event_category": "session_name",
                        "event_label": $body.data("session-namespace")
                    })

                    gtag("event", "Terminal/Reconnect", {
                        "event_category": "environment_name",
                        "event_label": $body.data("workshop-namespace")
                    })

                    gtag("event", "Terminal/Reconnect", {
                        "event_category": "training_portal",
                        "event_label": $body.data("training-portal")
                    })

                    gtag("event", "Terminal/Reconnect", {
                        "event_category": "ingress_domain",
                        "event_label": $body.data("ingress-domain")
                    })
                }
            }
        }

        this.socket.onmessage = async (evt) => {
            // If the socket isn't the one currently associated with the
            // terminal then bail out straight away as some sort of mixup has
            // occurred. Close the socket for good measure.

            if (this.socket === null) {
                console.warn("Connection was abandoned to terminal", this.id)
                socket.close()
                return
            }

            if (socket !== this.socket) {
                console.warn("Multiple connections to terminal", this.id)
                socket.close()
                return
            }

            let packet: Packet = JSON.parse(evt.data)

            if (packet.id == this.id) {
                switch (packet.type) {
                    case (PacketType.DATA): {
                        let args: InboundDataPacketArgs = packet.args

                        await this.write(args.data)

                        // Update the sequence number to that received on the
                        // DATA message from the server side. This affects
                        // what sequence number of sent on a HELLO message
                        // if we have to reconnect because the connection is
                        // dropped. It ensures that on reconnection we only
                        // get data we haven't seen before.

                        this.sequence = args.seq

                        break
                    }
                    case (PacketType.EXIT): {
                        console.log("Terminal has exited", this.id)

                        $(this.element).addClass("notify-exited")

                        $("#refresh-button").addClass("terminal-" + this.id + "-refresh-required")

                        this.scrollToBottom()
                        await this.write("\r\nExited\r\n")

                        this.socket.close()

                        this.shutdown = true
                        this.socket = null

                        // Generate analytics event to track terminal exit.

                        let $body = $("body")

                        send_analytics_event("Terminal/Exited", { terminal: this.id })

                        if ($body.data("google-tracking-id")) {
                            gtag("event", "Terminal/Exited", {
                                "event_category": "workshop_name",
                                "event_label": $body.data("workshop-name")
                            })

                            gtag("event", "Terminal/Exited", {
                                "event_category": "session_name",
                                "event_label": $body.data("session-namespace")
                            })

                            gtag("event", "Terminal/Exited", {
                                "event_category": "environment_name",
                                "event_label": $body.data("workshop-namespace")
                            })

                            gtag("event", "Terminal/Exited", {
                                "event_category": "training_portal",
                                "event_label": $body.data("training-portal")
                            })

                            gtag("event", "Terminal/Exited", {
                                "event_category": "ingress_domain",
                                "event_label": $body.data("ingress-domain")
                            })
                        }

                        break
                    }
                    case (PacketType.ERROR): {
                        let args: ErrorPacketArgs = packet.args

                        // Right now we only expect to receive reasons of
                        // "Forbidden" and "Hijacked". This is used to set
                        // an element class so can provide visual indicator
                        // to a user. Otherwise nothing is done for an error.

                        $(this.element).addClass(`notify-${args.reason.toLowerCase()}`)

                        break
                    }
                }
            }
            else {
                console.warn("Client session " + this.id + " received message for session " + packet.id)
            }
        }

        this.socket.onclose = (_evt: any) => {
            // If the socket isn't the one currently associated with the
            // terminal then bail out straight away as some sort of mixup has
            // occurred.

            if (socket !== this.socket)
                return

            let self = this

            // If the socket connection to the backend terminal server is
            // closed, it doesn't mean that the backend terminal session
            // has exited. The socket connection could have been lost due to
            // restart of a router between the frontend client and the
            // backend. This is in particular a problem when nginx is used
            // for ingress in a Kubernetes cluster. Every time a new ingress
            // is created, existing connections will at some point be dropped.
            // Usually this is about 4 minutes after a new ingress is added.
            // What we therefore do is attempt to reconnect, but where we
            // give up after 1 second. This is usually enough to transparently
            // recover from connections being dropped due to a router restart.
            // If reconnection fails, it truly means the backend session
            // had been terminated, or there was still an issue with a router.
            // In the latter case, a manual reconnection, or page refresh,
            // would need to be triggered.

            this.socket = null

            if (this.shutdown)
                return

            function connect() {
                if (this.shutdown)
                    return

                let parsed_url = url.parse(window.location.origin)

                let protocol = parsed_url.protocol == "https:" ? "wss" : "ws"
                let host = parsed_url.host
                let pathname = "/terminal/server"

                let server_url = `${protocol}://${host}${pathname}`

                console.log("Attempt re-connect to terminal", self.id)

                self.socket = new WebSocket(server_url)

                self.configure_handlers()
            }

            console.log("Terminal connection was lost", self.id)

            if (self.started !== null) {
                let finished = new Date()
                let duration = (finished.getTime() - self.started.getTime()) / 1000;

                console.log("Terminal session duration", duration)

                self.started = null
            }

            setTimeout(connect, 100)

            async function terminate() {
                self.reconnectTimer = null

                if (!self.reconnecting)
                    return

                console.log("Abandoning connection to terminal", self.id)

                self.reconnecting = false
                self.shutdown = true

                self.socket = null

                $(self.element).addClass("notify-closed")

                $("#refresh-button").addClass("terminal-" + self.id + "-refresh-required")

                self.scrollToBottom()
                await self.write("\r\nClosed\r\n")

                // Generate analytics event to track terminal close.

                let $body = $("body")

                send_analytics_event("Terminal/Closed", { terminal: this.id })

                if ($body.data("google-tracking-id")) {
                    gtag("event", "Terminal/Closed", {
                        "event_category": "workshop_name",
                        "event_label": $body.data("workshop-name")
                    })

                    gtag("event", "Terminal/Closed", {
                        "event_category": "session_name",
                        "event_label": $body.data("session-namespace")
                    })

                    gtag("event", "Terminal/Closed", {
                        "event_category": "environment_name",
                        "event_label": $body.data("workshop-namespace")
                    })

                    gtag("event", "Terminal/Closed", {
                        "event_category": "training_portal",
                        "event_label": $body.data("training-portal")
                    })

                    gtag("event", "Terminal/Closed", {
                        "event_category": "ingress_domain",
                        "event_label": $body.data("ingress-domain")
                    })
                }
            }

            if (!this.reconnecting) {
                console.log("Trigger reconnection timeout for terminal", self.id)

                self.reconnectTimer = setTimeout(terminate, 10000)

                this.reconnecting = true
            }
        }
    }

    private configure_sensors() {
        // This monitors the element the terminal is embedded in for
        // changes in size and triggers a recalculation of the terminal
        // size. In order to avoid problems with multiple resize events
        // occuring, the callbacks are throttled so at most one is
        // allowed in the specified time period.

        this.sensor = new ResizeSensor(this.element, _.throttle(() => {
            this.resize_terminal()
        }, 500))
    }

    private initiate_pings() {
        let self = this

        // Ping messages are only sent from client to backend server. Some
        // traffic is required when the session is otherwise idle, else you
        // can't tell if the connection has been dropped.

        function ping() {
            self.send_message(PacketType.PING)
            setTimeout(ping, 15000)
        }

        setTimeout(ping, 15000)
    }

    private resize_terminal() {
        // As long as the dimensions are valid, the terminal is re-fit to
        // the element size and a RESIZE message is sent to the backend
        // server. The dimensions on the server side are using to notify
        // the psudeo tty for the terminal process of the change in window
        // dimenions allowing any application to adjust to the new size
        // and refresh the terminal screen.  

        if (this.element.clientWidth > 0 && this.element.clientHeight > 0) {
            this.fitter.fit()

            let args: ResizePacketArgs = {
                cols: this.terminal.cols,
                rows: this.terminal.rows
            }

            this.send_message(PacketType.RESIZE, args)
        }
    }

    private send_message(type: PacketType, args?: any): boolean {
        if (!this.socket)
            return false

        if (this.socket.readyState === WebSocket.OPEN) {
            let packet: Packet = {
                type: type,
                id: this.id
            }

            if (args !== undefined)
                packet["args"] = args

            this.socket.send(JSON.stringify(packet))

            return true
        }

        return false
    }

    async write(text: string) {
        let self = this

        function writeSync(text: string | Uint8Array): Promise<void> {
            return new Promise<void>(resolve => self.terminal.write(text, resolve));
        }

        await writeSync(text)
    }

    focus() {
        this.terminal.focus()
    }

    clear() {
        this.terminal.clear()
    }

    scrollToBottom() {
        this.terminal.scrollToBottom()
    }

    async paste(text: string, bracketed: boolean = true) {
        if (!this.blocked) {
            if (this.terminal.modes.bracketedPasteMode && !bracketed) {
                await this.write("\x1b[?2004l").then(_ => {
                    this.terminal.paste(text)
                }).then(async _ => {
                    await this.write("\x1b[?2004h")
                })
            }
            else {
                await this.terminal.paste(text)
            }
        } else
            this.buffer.push({ text: text, bracketed: bracketed })
    }

    close() {
        if (this.socket)
            this.socket.close()
    }

    reconnect() {
        if (!this.shutdown)
            return

        // Where the socket connection had previously been lost and an
        // automatic reconnect didn't work, this allows a new attempt to
        // reconnect to be made.

        this.shutdown = false
        this.sequence = 0

        let self = this

        console.log("Request to force reconnect terminal", self.id)

        function connect() {
            if (this.shutdown)
                return

            let parsed_url = url.parse(window.location.origin)

            let protocol = parsed_url.protocol == "https:" ? "wss" : "ws"
            let host = parsed_url.host
            let pathname = "/terminal/server"

            let server_url = `${protocol}://${host}${pathname}`

            console.log("Attempt force re-connect to terminal", self.id)

            self.socket = new WebSocket(server_url)

            self.configure_handlers()
        }

        setTimeout(connect, 100)

        function terminate() {
            self.reconnectTimer = null

            if (!self.reconnecting)
                return

            console.log("Abandoning connection to terminal", self.id)

            self.reconnecting = false
            self.shutdown = true

            self.socket = null
        }

        if (!this.reconnecting) {
            console.log("Trigger reconnection timeout for terminal", self.id)

            self.reconnectTimer = setTimeout(terminate, 5000)

            this.reconnecting = true
        }
    }

    set_option(name: string, value: any) {
        this.terminal.setOption(name, value)
    }
}

class Terminals {
    sessions: { [id: string]: TerminalSession } = {}

    constructor() {
        // Search for all elements with class "terminal". For these we insert
        // a terminal directly into the page connected using a web socket.
        // Since we are using a class, there can be multiple instances. The
        // id of the terminal session being connected to is taken from the
        // "session-id" data attribute. The "endpoint-id" is a unique value
        // identifying the particular terminal server backend. It acts as a
        // crude method of ensuring that a frontend client is talking to the
        // correct backend since they must match.

        $(".terminal").each((index: number, element: HTMLElement) => {
            this.initialize_terminal(element)
        })
    }

    initialize_terminal(element: HTMLElement) {
        let $body = $("body")
        let context = $body.data("user-context")
        let id: string = $(element).data("session-id")
        let endpoint: string = $(element).data("endpoint-id")

        console.log("Initializing terminal", id)

        this.sessions[id] = new TerminalSession(context, id, element, endpoint)

        // Append a div to element with translucent text overlaid on
        // the terminal. Only applies to terminals sessions 1-3.

        let overlay = $(`<div class="terminal-overlay
                terminal-overlay-${id}"></div>`)[0]

        element.append(overlay)
    }

    // The following are the only APIs which separate frontend application
    // code should use to interact with terminals.

    async paste_to_terminal(text: string, id: string = "1") {
        let terminal = this.sessions[id]

        if (terminal)
            await terminal.paste(text)
    }

    async paste_to_all_terminals(text: string) {
        await this.paste_to_terminal(text, "1")
        await this.paste_to_terminal(text, "2")
        await this.paste_to_terminal(text, "3")
    }

    async interrupt_terminal(id: string = "1") {
        let terminal = this.sessions[id]

        if (terminal) {
            terminal.scrollToBottom()
            await terminal.paste(String.fromCharCode(0x03))
        }
    }

    interrupt_all_terminals() {
        this.interrupt_terminal("1")
        this.interrupt_terminal("2")
        this.interrupt_terminal("3")
    }

    clear_terminal(id: string = "1") {
        let terminal = this.sessions[id]

        if (terminal) {
            terminal.scrollToBottom()
            terminal.clear()
        }
    }

    clear_all_terminals() {
        this.clear_terminal("1")
        this.clear_terminal("2")
        this.clear_terminal("3")
    }

    async execute_in_terminal(command: string, id: string = "1", clear: boolean = false) {
        if (command == "<ctrl-c>" || command == "<ctrl+c>")
            return this.interrupt_terminal(id)

        let terminal = this.sessions[id]

        if (terminal) {
            terminal.scrollToBottom()

            if (clear)
                terminal.clear()

            await terminal.paste(command + "\r", false)
        }
    }

    async execute_in_all_terminals(command: string, clear: boolean = false) {
        if (command == "<ctrl-c>" || command == "<ctrl+c>")
            return this.interrupt_all_terminals()

        await this.execute_in_terminal(command, "1")
        await this.execute_in_terminal(command, "2")
        await this.execute_in_terminal(command, "3")
    }

    disconnect_terminal(id: string = "1") {
        let terminal = this.sessions[id]

        if (terminal)
            terminal.close()
    }

    disconnect_all_terminals() {
        for (let id in this.sessions)
            this.sessions[id].close()
    }

    reconnect_terminal(id: string = "1") {
        let terminal = this.sessions[id]

        if (terminal)
            terminal.reconnect()
    }

    reconnect_all_terminals() {
        for (let id in this.sessions)
            this.sessions[id].reconnect()
    }

    set_option_all_terminals(name: string, value: any) {
        for (let id in this.sessions) {
            this.sessions[id].set_option(name, value)
        }
    }
}

class Dashboard {
    private dashboard: any
    private expiration: number
    private extendable: boolean
    private expiring: boolean

    constructor() {
        if ($("#dashboard").length) {
            // To indicate progress, update message on startup cover panel. Also
            // hide the cover panel after 15 seconds if we don't get through all
            // the dashboard configuration for some reason or if the user
            // changes browser tab when it is starting, which can sometimes
            // result in the notification that page has loaded being dropped by
            // the browser.

            setTimeout(() => {
                $("#startup-cover-panel-message>h5").text("Configuring workshop...")
            }, 1000)

            setTimeout(() => {
                $("#startup-cover-panel").hide()
            }, 15000)

            // The web interface can either have a workshop panel on the left
            // and workarea panel on the right, or it can have just a workarea
            // panel. If there is both, we need to split the two

            console.log("Adding split for workshop/workarea")

            if ($("#workshop-panel").length) {
                this.dashboard = Split(["#workshop-panel", "#workarea-panel"], {
                    gutterSize: 8,
                    sizes: [35, 65],
                    cursor: "col-resize",
                    direction: "horizontal",
                    snapOffset: 120,
                    minSize: 0
                })
            }

            // Add action whereby if double click on vertical divider, will
            // either collapse or expand the workshop panel.

            $("#workshop-panel").next("div.gutter-horizontal").on("dblclick", () => {
                if (this.dashboard.getSizes()[0] < 5.0)
                    this.dashboard.setSizes([35, 65])
                else
                    this.dashboard.collapse(0)
            })

            // If the terminal layout is "lower", then the terminal is being
            // deployed the main workarea, so need to split the workarea.

            console.log("Adding split for terminal below workarea")

            if ($("#workarea-1").length && $("#workarea-2").length) {
                Split(["#workarea-1", "#workarea-2"], {
                    gutterSize: 8,
                    sizes: [70, 30],
                    cursor: "row-resize",
                    direction: "vertical"
                })
            }
        }

        if ($("#terminal-1").length)
            console.log("One or more terminals enabled")

        if ($("#terminal-3").length) {
            console.log("Adding split for three terminals")

            Split(["#terminal-1", "#terminal-2", "#terminal-3"], {
                gutterSize: 8,
                sizes: [50, 25, 25],
                cursor: "row-resize",
                direction: "vertical"
            })
        }
        else if ($("#terminal-2").length) {
            console.log("Adding split for two terminals")

            Split(["#terminal-1", "#terminal-2"], {
                gutterSize: 8,
                sizes: [60, 40],
                cursor: "row-resize",
                direction: "vertical"
            })
        }

        // Add a click action to any panel with a child iframe set up for
        // delayed loading when first click performed.

        $("iframe[data-src]").each(function () {
            let iframe = $(this)
            let trigger = iframe.parent().attr("aria-labelledby")
            if (trigger) {
                $("#" + trigger).on("click", () => {
                    if (iframe.data("src")) {
                        iframe.prop("src", iframe.data("src"))
                        iframe.data("src", "")
                    }
                })
            }
        })

        // Add a click action to confirmation button of exit/finish workshop
        // dialog in order to generate analytics event and redirect browser
        // back to portal for possible deletion of the workshop session.

        $("#terminate-session-dialog-confirm").on("click", (event) => {
            let $body = $("body")

            send_analytics_event("Workshop/Terminate")

            if ($body.data("google-tracking-id")) {
                gtag("event", "Workshop/Terminate", {
                    "event_category": "workshop_name",
                    "event_label": $body.data("workshop-name")
                })

                gtag("event", "Workshop/Terminate", {
                    "event_category": "session_name",
                    "event_label": $body.data("session-namespace")
                })

                gtag("event", "Workshop/Terminate", {
                    "event_category": "environment_name",
                    "event_label": $body.data("workshop-namespace")
                })

                gtag("event", "Workshop/Terminate", {
                    "event_category": "training_portal",
                    "event_label": $body.data("training-portal")
                })

                gtag("event", "Workshop/Terminate", {
                    "event_category": "ingress_domain",
                    "event_label": $body.data("ingress-domain")
                })
            }

            window.top.location.href = $(event.target).data("restart-url")
        })

        $("#finished-workshop-dialog-confirm").on("click", (event) => {
            let $body = $("body")

            send_analytics_event("Workshop/Finish")

            if ($body.data("google-tracking-id")) {
                gtag("event", "Workshop/Finish", {
                    "event_category": "workshop_name",
                    "event_label": $body.data("workshop-name")
                })

                gtag("event", "Workshop/Finish", {
                    "event_category": "session_name",
                    "event_label": $body.data("session-namespace")
                })

                gtag("event", "Workshop/Finish", {
                    "event_category": "environment_name",
                    "event_label": $body.data("workshop-namespace")
                })

                gtag("event", "Workshop/Finish", {
                    "event_category": "training_portal",
                    "event_label": $body.data("training-portal")
                })

                gtag("event", "Workshop/Finish", {
                    "event_category": "ingress_domain",
                    "event_label": $body.data("ingress-domain")
                })
            }

            window.top.location.href = $(event.target).data("restart-url")
        })

        // Add a click action to confirmation button of expired workshop
        // dialog to redirect browser back to portal.

        $("#workshop-expired-dialog-confirm").on("click", (event) => {
            window.top.location.href = $(event.target).data("restart-url")
        })

        // Add a click action for the expand button to enable making full
        // screen or exiting full screen.

        if (document.fullscreenEnabled) {
            $("#fullscreen-button").on("click", (event) => {
                let $button = $("#fullscreen-button")
                if ($button.hasClass("fa-expand-arrows-alt")) {
                    if (document.documentElement.requestFullscreen) {
                        document.documentElement.requestFullscreen()
                        if (event.shiftKey) {
                            terminals.set_option_all_terminals("theme", {
                                background: '#fafafa',
                                foreground: '#000000',
                                cursor: '#000000'
                            })
                        }
                    }
                }
                else if ($button.hasClass("fa-compress-arrows-alt")) {
                    if (document.exitFullscreen) {
                        document.exitFullscreen()
                    }
                }
            })

            $(document).on("fullscreenchange", () => {
                let $button = $("#fullscreen-button")
                if (document.fullscreenElement) {
                    $button.addClass("fa-compress-arrows-alt")
                    $button.removeClass("fa-expand-arrows-alt")
                }
                else {
                    $button.addClass("fa-expand-arrows-alt")
                    $button.removeClass("fa-compress-arrows-alt")
                    terminals.set_option_all_terminals("theme", {
                        background: '#000000',
                        foreground: '#ffffff',
                        cursor: '#ffffff'
                    })
                }
            })
        }
        else {
            $("#fullscreen-button").hide()
        }

        // Add a click action for the refresh button to enable reloading
        // of workshop content, terminals or exposed tab.

        $("#refresh-button").on("click", (event) => {
            if (event.shiftKey) {
                if (this.dashboard) {
                    // If shift is pressed we target the workshop panel,
                    // either reloading it, or expanding the panel if it
                    // was previously collapsed.

                    if (this.dashboard.getSizes()[0] >= 5.0) {
                        let iframe = $("#workshop-iframe")
                        let iframe_window: any = iframe.contents().get(0)
                        iframe_window.location.reload()
                    }
                    else {
                        this.dashboard.setSizes([35, 65])
                    }
                }
            }
            else {
                // If terminal layout is "lower" and terminals are candidates
                // for reconnecting, then reconnect the terminals rather than
                // refresh the dashboard.

                let $body = $("body")
                let reconnect = false

                if ($(event.target).is("[class$='-refresh-required']"))
                    reconnect = true

                if ($body.data("terminal-layout") == "lower" && reconnect) {
                    terminals.reconnect_all_terminals()
                }
                else {
                    let active = $("#workarea-navbar-div li a.active")

                    if (active.length) {
                        if (active.attr("id") != "terminal-tab") {
                            let href = active.attr("href")
                            if (href) {
                                let terminal = $(href + " div.terminal")
                                if (terminal) {
                                    terminals.reconnect_terminal(terminal.data("session-id"))
                                }
                                else {
                                    let iframe = $(href + " iframe")
                                    if (iframe.length)
                                        iframe.attr("src", iframe.attr("src"))
                                }
                            }
                        }
                        else {
                            terminals.reconnect_all_terminals()
                        }
                    }
                }
            }
        })

        // Add a click action to menu items for opening target URL in a
        // separate window.

        $(".open-window").on("click", (event) => {
            window.open($(event.target).data("url"))
        })

        // Initiate countdown timer if enabled for workshop session. Also
        // add a click action to the button so the workshop session can be
        // extended.

        let self = this

        function check_countdown() {
            function current_time() {
                return Math.floor(new Date().getTime() / 1000)
            }

            function time_remaining() {
                let now = current_time()
                return Math.max(0, self.expiration - now)
            }

            function format_time_digits(num: number, pad: boolean = true) {
                if (num < 10 && pad) {
                    let s = "0" + num
                    return s.substr(s.length - 2)
                }
                else {
                    return num.toString()
                }
            }

            function format_countdown(countdown: number) {
                let text = ' '

                let hours = Math.floor(countdown / (60 * 60))
                let minutes = Math.floor((countdown - (hours * 60 * 60)) / 60)
                let seconds = countdown % 60

                if (hours) {
                    text = text + format_time_digits(hours, false)
                    text = text + ':' + format_time_digits(minutes)
                }
                else {
                    text = text + format_time_digits(minutes)
                }

                text = text + ':' + format_time_digits(seconds)

                return text
            }

            let button = $("#countdown-button")
            let update = false

            if (self.expiration !== undefined) {
                let countdown = time_remaining()

                button.html(format_countdown(countdown))
                button.removeClass('d-none')

                // let extendable = self.extendable

                // if (extendable === undefined)
                //     extendable = countdown <= 300

                if (self.expiring) {
                    if (self.extendable) {
                        button.addClass("btn-warning")
                        button.removeClass("btn-default")
                        button.removeClass("btn-transparent")
                        button.removeClass("btn-danger")
                    }
                    else {
                        button.addClass("btn-danger")
                        button.removeClass("btn-default")
                        button.removeClass("btn-transparent")
                        button.removeClass("btn-warning")
                    }
                }
                else {
                    button.addClass("btn-default")
                    button.addClass("btn-transparent")
                    button.removeClass("btn-warning")
                    button.removeClass("btn-danger")
                }

                if (countdown && !((countdown + 2) % 15))
                    update = true

                if (countdown <= 0) {
                    if (!$("#workshop-expired-dialog").data("expired")) {
                        $("#workshop-expired-dialog").data("expired", "true")

                        $("#workshop-failed-dialog").modal("hide")

                        $("#workshop-expired-dialog").modal("show")

                        let $body = $("body")

                        send_analytics_event("Workshop/Expired")

                        if ($body.data("google-tracking-id")) {
                            gtag("event", "Workshop/Expired", {
                                "event_category": "workshop_name",
                                "event_label": $body.data("workshop-name")
                            })

                            gtag("event", "Workshop/Expired", {
                                "event_category": "session_name",
                                "event_label": $body.data("session-namespace")
                            })

                            gtag("event", "Workshop/Expired", {
                                "event_category": "environment_name",
                                "event_label": $body.data("workshop-namespace")
                            })

                            gtag("event", "Workshop/Expired", {
                                "event_category": "training_portal",
                                "event_label": $body.data("training-portal")
                            })

                            gtag("event", "Workshop/Expired", {
                                "event_category": "ingress_domain",
                                "event_label": $body.data("ingress-domain")
                            })
                        }
                    }
                }
            }
            else {
                button.addClass('d-none')
                button.html('')

                update = true
            }

            if (update) {
                $.ajax({
                    type: 'GET',
                    url: "/session/schedule",
                    cache: false,
                    success: (data, textStatus, xhr) => {
                        if (data.expires) {
                            let now = current_time()
                            let countdown = Math.max(0, Math.floor(data.countdown))
                            self.expiration = now + countdown
                            self.extendable = data.extendable
                            self.expiring = data.expiring
                        }

                        setTimeout(check_countdown, 500)
                    },
                    error: () => {
                        setTimeout(check_countdown, 500)
                    }
                })
            }
            else {
                setTimeout(check_countdown, 500)
            }
        }

        if ($("#countdown-button").length) {
            setTimeout(check_countdown, 500)

            $("#countdown-button").on("click", () => {
                $.ajax({
                    type: 'GET',
                    url: "/session/extend",
                    cache: false,
                    success: (data, textStatus, xhr) => {
                        if (data.expires) {
                            let now = Math.floor(new Date().getTime() / 1000)
                            let countdown = Math.max(0, Math.floor(data.countdown))
                            self.expiration = now + countdown
                            self.extendable = data.extendable
                            self.expiring = data.expiring
                            let button = $("#countdown-button")
                            button.addClass("btn-default")
                            button.addClass("btn-transparent")
                            button.removeClass("btn-danger")
                            button.removeClass("btn-warning")
                        }
                    },
                    error: () => { }
                })
            })
        }

        // Hide the startup cover panel across the dashboard once the page has
        // finished loading. The cover panel hides adjustments in dashboard as
        // it is being displayed.

        $(window).on('load', () => {
            setTimeout(() => {
                $("#startup-cover-panel").hide()
            }, 1000)

            let $body = $("body")

            if ($body.data("workshop-ready") == false) {
                $("#workshop-failed-dialog").modal("show")
            }
            else if ($body.data("page-hits") == "1") {
                $("#started-workshop-dialog").modal("show")
            }
        })

        // Select whatever is the first tab of the navbar so it is displayed.

        $($("#workarea-nav>li>a")[0]).trigger("click")
    }

    session_owner(): string {
        return $("body").data("session-owner")
    }

    finished_workshop() {
        $("#finished-workshop-dialog").modal("show")
    }

    verify_origin(origin: string): boolean {
        if (origin == window.origin)
            return true

        let result = false

        let $body = $("body")
        let workshop_url = $body.data("workshop-url")

        if (workshop_url && workshop_url.match(/^https?:/)) {
            let url = new URL(workshop_url)

            if (origin == url.origin) {
                result = true
            }
        }

        $(".dashboard-iframe").each((index: number, element: HTMLElement) => {
            let src = element.dataset["src"]

            if (src) {
                let url = new URL(src)

                if (origin == url.origin) {
                    result = true
                    return false
                }
            }
        })

        return result
    }

    preview_image(src: string, title: string) {
        $("#preview-image-element").attr("src", src)
        $("#preview-image-title").text(title)
        $("#preview-image-dialog").modal("show")
    }

    reload_dashboard(name: string, url?: string): boolean {
        let id = string_to_slug(name)

        if (!this.expose_dashboard(id))
            return false

        if (name != "terminal") {
            let tab = $(`#${id}-tab`)
            let href = tab.attr("href")
            if (href) {
                let terminal = $(href + " div.terminal")
                if (terminal.length) {
                    terminals.reconnect_terminal(terminal.data("session-id"))
                }
                else {
                    let iframe = $(href + " iframe")
                    if (iframe.length)
                        iframe.attr("src", url || iframe.attr("src"))
                }
            }
        }
        else {
            terminals.reconnect_all_terminals()
        }

        return true
    }

    expose_terminal(name: string): boolean {
        name = String(name)

        let id = string_to_slug(name)

        let terminal = $(`#terminal-${id}`)

        let tab_anchor = $(`#${terminal.data("tab")}`)

        if (!tab_anchor.length)
            return false

        tab_anchor.trigger("click")

        return true
    }

    expose_dashboard(name: string): boolean {
        let id = string_to_slug(name)

        let tab_anchor = $(`#${id}-tab`)

        if (!tab_anchor.length)
            return false

        tab_anchor.trigger("click")

        return true
    }

    create_dashboard(name: string, url: string): boolean {
        if (!name)
            return

        let id = string_to_slug(name)

        // Make sure dashboard with desired name doesn't already exist.

        if ($(`#${id}-tab`).length)
            return false

        // Work out if embedding a terminal or external site reference.

        let terminal: string = null

        if (url.startsWith("terminal:")) {
            terminal = url.replace("terminal:", "")
            url = null
        }

        if (!terminal)
            url = url || "about:blank"

        // Create new tab. The button needs to be insert before the
        // "#workarea-controls". The panel and iframe need to be added at
        // the end of "#workarea-panels".

        let tab_li = $(`<li class="nav-item"></li>`)

        let tab_anchor = $(`<a class="nav-link" id="${id}-tab"
            data-toggle="tab" href="#${id}-panel" role="tab"
            aria-controls="${id}-panel" data-transient-tab="true"></a>`).text(name)

        tab_li.append(tab_anchor)

        let panel_div = $(`<div id="${id}-panel"
            class="tab-pane fade show panel-div iframe-div"
            role="tabpanel" aria-labelledby="${id}-tab"></div>`)

        if (terminal) {
            let $body = $("body")
            let endpoint_id = $body.data("endpoint-id")

            let terminal_div = $(`<div class="terminal"
                id="terminal-${terminal}"
                data-endpoint-id="${endpoint_id}"
                data-session-id="${terminal}"
                data-tab="${id}-tab"></div>`)

            panel_div.append(terminal_div)

            terminals.initialize_terminal(terminal_div[0])
        }
        else {
            let iframe_div = $(`<iframe class="dashboard-iframe" src="${url}" data-src="${url}"></iframe>`)

            panel_div.append(iframe_div)
        }

        $("#workarea-controls").before(tab_li)
        $("#workarea-panels").append(panel_div)

        // Now trigger click action on the tab to expose new dashboard tab.

        tab_anchor.trigger("click")

        return true
    }

    delete_dashboard(name: string): boolean {
        let id = string_to_slug(name)

        let tab_anchor = $(`#${id}-tab`)
        let panel_div = $(`#${id}-panel`)

        // Make sure dashboard with desired name exists and that it is a
        // transient tab that can be deleted.

        if (!tab_anchor.length || !tab_anchor.data("transient-tab"))
            return false

        // Remove tab and panel. It is actually parent of the tab that needs
        // to be removed

        tab_anchor.parent().remove()
        panel_div.remove()

        // If tab is active, revert back to the first dashboard tab.

        if (tab_anchor.hasClass("active"))
            $($("#workarea-nav>li>a")[0]).trigger("click")

        return true
    }

    reload_terminal() {
        this.reload_dashboard("terminal")
    }

    reload_workshop() {
        if (this.dashboard) {
            if (this.dashboard.getSizes()[0] >= 5.0) {
                let iframe = $("#workshop-iframe")
                let iframe_window: any = iframe.contents().get(0)
                iframe_window.location.reload()
            }
            else {
                this.dashboard.setSizes([35, 65])
            }
        }
    }

    collapse_workshop() {
        if (this.dashboard)
            this.dashboard.collapse(0)
    }
}

export let dashboard: Dashboard
export let terminals: Terminals

interface TerminalExecuteOptions {
    command: string;
    session: string
    clear: boolean
}

interface TerminalExecuteAllOptions {
    command: string
    clear: boolean
}

interface TerminalSelectOptions {
    session: string;
}

interface TerminalPasteOptions {
    text: string
    session: string
}

interface DashboardSelectOptions {
    name: string
}

interface DashboardCreateOptions {
    name: string
    url: string
}

const action_table = {
    "terminal:execute": async function (args: TerminalExecuteOptions) {
        let id = args.session || "1"
        if (id == "*") {
            dashboard.expose_dashboard("terminal")
            terminals.execute_in_all_terminals(args.command, args.clear)
        }
        else {
            dashboard.expose_terminal(id)
            await terminals.execute_in_terminal(args.command, id, args.clear)
        }
    },
    "terminal:execute-all": async function (args: TerminalExecuteAllOptions) {
        dashboard.expose_dashboard("terminal")
        await terminals.execute_in_all_terminals(args.command, args.clear)
    },
    "terminal:clear": function (args: TerminalSelectOptions) {
        let id = args.session || "1"
        if (id == "*") {
            dashboard.expose_dashboard("terminal")
            terminals.clear_all_terminals()
        }
        else {
            dashboard.expose_terminal(id)
            terminals.clear_terminal(id)
        }
    },
    "terminal:clear-all": function () {
        dashboard.expose_dashboard("terminal")
        terminals.clear_all_terminals()
    },
    "terminal:interrupt": function (args: TerminalSelectOptions) {
        let id = args.session || "1"
        if (id == "*") {
            dashboard.expose_dashboard("terminal")
            terminals.interrupt_all_terminals()
        }
        else {
            dashboard.expose_terminal(id)
            terminals.interrupt_terminal(id)
        }
    },
    "terminal:interrupt-all": function () {
        dashboard.expose_dashboard("terminal")
        terminals.interrupt_all_terminals()
    },
    "terminal:input": function (args: TerminalPasteOptions) {
        dashboard.expose_terminal(args.session)
        terminals.paste_to_terminal(args.text, args.session)
    },
    "dashboard:open-dashboard": function (args: DashboardSelectOptions) {
        dashboard.expose_dashboard(args.name)
    },
    "dashboard:create-dashboard": function (args: DashboardCreateOptions) {
        dashboard.create_dashboard(args.name, args.url)
    },
    "dashboard:delete-dashboard": function (args: DashboardSelectOptions) {
        dashboard.delete_dashboard(args.name)
    },
    "dashboard:reload-dashboard": function (args: DashboardCreateOptions) {
        dashboard.reload_dashboard(args.name, args.url)
    },
}

window.addEventListener("message", function (event) {
    if (dashboard.verify_origin(event.origin)) {
        let handler = action_table[event.data.action]
        if (handler !== undefined)
            handler(event.data.data)
    }
})

function initialize_dashboard() {
    console.log("Initalizing dashboard")

    dashboard = new Dashboard()

    console.log("Initializing terminals")

    terminals = new Terminals()
}

$(document).ready(() => {
    // Generate analytics events if a tracking ID is provided.

    let $body = $("body")

    send_analytics_event("Workshop/Load")

    if ($body.data("page-hits") == "1")
        send_analytics_event("Workshop/Start")

    if ($body.data("google-tracking-id")) {
        gtag("set", {
            "custom_map": {
                "dimension1": "workshop_name",
                "dimension2": "session_name",
                "dimension3": "environment_name",
                "dimension4": "training_portal",
                "dimension5": "ingress_domain",
                "dimension6": "ingress_protocol"
            }
        })

        let gsettings = {
            "workshop_name": $body.data("workshop-name"),
            "session_name": $body.data("session-namespace"),
            "environment_name": $body.data("workshop-namespace"),
            "training_portal": $body.data("training-portal"),
            "ingress_domain": $body.data("ingress-domain"),
            "ingress_protocol": $body.data("ingress-protocol")
        }

        if ($body.data("ingress-protocol") == "https")
            gsettings["cookie_flags"] = "max-age=86400;secure;samesite=none"

        gtag("config", $body.data("google-tracking-id"), gsettings)

        gtag("event", "Workshop/Load", {
            "event_category": "workshop_name",
            "event_label": $body.data("workshop-name")
        })

        gtag("event", "Workshop/Load", {
            "event_category": "session_name",
            "event_label": $body.data("session-namespace")
        })

        gtag("event", "Workshop/Load", {
            "event_category": "environment_name",
            "event_label": $body.data("workshop-namespace")
        })

        gtag("event", "Workshop/Load", {
            "event_category": "training_portal",
            "event_label": $body.data("training-portal")
        })

        gtag("event", "Workshop/Load", {
            "event_category": "ingress_domain",
            "event_label": $body.data("ingress-domain")
        })

        if ($body.data("page-hits") == "1") {
            gtag("event", "Workshop/Start", {
                "event_category": "workshop_name",
                "event_label": $body.data("workshop-name")
            })

            gtag("event", "Workshop/Start", {
                "event_category": "session_name",
                "event_label": $body.data("session-namespace")
            })

            gtag("event", "Workshop/Start", {
                "event_category": "environment_name",
                "event_label": $body.data("workshop-namespace")
            })

            gtag("event", "Workshop/Start", {
                "event_category": "training_portal",
                "event_label": $body.data("training-portal")
            })

            gtag("event", "Workshop/Start", {
                "event_category": "ingress_domain",
                "event_label": $body.data("ingress-domain")
            })
        }
    }

    if ($body.data("clarity-tracking-id")) {
        clarity("set", "workshop_name", $body.data("workshop-name"))
        clarity("set", "session_name", $body.data("session-namespace"))
        clarity("set", "environment_name", $body.data("workshop-namespace"))
        clarity("set", "training_portal", $body.data("training-portal"))
        clarity("set", "ingress_domain", $body.data("ingress-domain"))
        clarity("set", "ingress_protocol", $body.data("ingress-protocol"))
    }

    // In order to support use of "powerline" tool for fancy shell prompts
    // we need to use a custom font with modifications for special glyphs
    // used by powerline. Because fonts usually only load when a browser
    // first detects the font is required, this usually results in fonts
    // being wrongly displayed if first time a user is using this. To avoid
    // that we use a font loader to explicitly load the fonts first before
    // start initializing the terminals.

    let font_400 = new FontFaceObserver("SourceCodePro", { weight: 400 });
    let font_700 = new FontFaceObserver("SourceCodePro", { weight: 700 });

    let font_400_loader = font_400.load()
    let font_700_loader = font_700.load()

    font_400_loader.then(() => {
        font_700_loader.then(() => {
            console.log("Loaded fonts okay")
            initialize_dashboard()
        }), () => {
            console.log("Failed to load fonts")
            initialize_dashboard()
        }
    }), () => {
        font_700_loader.then(() => {
            console.log("Failed to load fonts")
            initialize_dashboard()
        }), () => {
            console.log("Failed to load fonts")
            initialize_dashboard()
        }
    }
})
