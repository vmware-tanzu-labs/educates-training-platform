import * as $ from "jquery"
import * as url from "url"

import { Terminal } from "xterm"
import { FitAddon } from "xterm-addon-fit"
import { WebLinksAddon } from "xterm-addon-web-links"

import { ResizeSensor } from "css-element-queries"

const FontFaceObserver = require("fontfaceobserver")

const _ = require("lodash")

const Split = require("split.js")

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

class TerminalSession {
    private id: string
    private element: HTMLElement
    private endpoint: string
    private terminal: Terminal
    private fitter: FitAddon
    private sensor: ResizeSensor
    private socket: WebSocket
    private sequence: number
    private reconnecting: boolean
    private shutdown: boolean

    constructor(id: string, element: HTMLElement, endpoint: string) {
        this.id = id
        this.element = element
        this.endpoint = endpoint
        this.sequence = -1

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

        this.socket = new WebSocket(server_url)

        this.configure_handlers()
        this.configure_sensors()

        // If there is more than one terminal session, if this is the first
        // session ensure it grabs focus. Does mean that if creating extra
        // sessions in separate window that they will not grab focus. Is
        // better than a secondary session grabbing focus when have more than
        // on the page.

        if (this.id == "1")
            this.focus()
    }

    private configure_handlers() {
        if (this.shutdown)
            return

        $(this.element).removeClass("notify-closed")
        $(this.element).removeClass("notify-exited")

        this.socket.onopen = () => {
            this.reconnecting = false

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
                this.terminal.onData((data) => {
                    let args: OutboundDataPacketArgs = { data: data }
                    this.send_message(PacketType.DATA, args)
                })

                this.initiate_pings()

                // Set sequence number to 0 so we don't do this all again.

                this.sequence = 0
            }
        }

        this.socket.onmessage = (evt) => {
            let packet: Packet = JSON.parse(evt.data)

            if (packet.id == this.id) {
                switch (packet.type) {
                    case (PacketType.DATA): {
                        let args: InboundDataPacketArgs = packet.args

                        this.terminal.write(args.data)

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
                        console.log('EXIT')

                        $(this.element).addClass("notify-exited")

                        this.scrollToBottom()
                        this.write("\r\nExited\r\n")

                        this.socket.close()

                        this.shutdown = true
                        this.socket = null
                        
                        break
                    }
                    case (PacketType.ERROR): {
                        let args: ErrorPacketArgs = packet.args

                        // Right now we only expect to receive reasons of
                        // 'Forbidden' and 'Hijacked'. This is used to set
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

                let url = window.location.origin

                url = url.replace("https://", "wss://")
                url = url.replace("http://", "ws://")

                self.socket = new WebSocket(url)

                self.configure_handlers()
            }

            this.reconnecting = true

            setTimeout(connect, 100)

            function terminate() {
                if (!self.reconnecting)
                    return

                self.reconnecting = false
                self.shutdown = true

                $(self.element).addClass("notify-closed")

                self.scrollToBottom()
                self.write("\r\nClosed\r\n")
            }

            setTimeout(terminate, 1000)
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

    write(text: string) {
        this.terminal.write(text)
    }

    focus() {
        this.terminal.focus()
    }

    scrollToBottom() {
        this.terminal.scrollToBottom()
    }

    paste(text: string) {
        this.terminal.paste(text)
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

        function connect() {
            if (this.shutdown)
                return

            let url = window.location.origin

            url = url.replace("https://", "wss://")
            url = url.replace("http://", "ws://")

            self.socket = new WebSocket(url)

            self.configure_handlers()
        }

        this.reconnecting = true

        setTimeout(connect, 100)

        function terminate() {
            if (!self.reconnecting)
                return

            self.reconnecting = false
            self.shutdown = true
        }

        setTimeout(terminate, 1000)
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
        // identify the particular terminal server backend. It acts as a
        // crude method of ensuring that a frontend client is talking to the
        // correct backend since they must match.

        $(".terminal").each((index: number, element: HTMLElement) => {
            let id: string = $(element).data("session-id")
            let endpoint: string = $(element).data("endpoint-id")

            this.sessions[id] = new TerminalSession(id, element, endpoint)
        })
    }

    // The following are the only APIs which separate frontend application
    // code should use to interact with terminals.

    paste_to_terminal(text: string, id: string = "1") {
        let terminal = this.sessions[id]

        if (terminal)
            terminal.paste(text)
    }

    paste_to_all_terminals(text: string) {
        for (let id in this.sessions)
            this.sessions[id].paste(text)
    }

    interrupt_terminal(id: string = "1") {
        let terminal = this.sessions[id]

        if (terminal) {
            terminal.scrollToBottom()
            terminal.paste(String.fromCharCode(0x03))
        }
    }

    interrupt_all_terminals() {
        for (let id in this.sessions) {
            let terminal = this.sessions[id]
            terminal.scrollToBottom()
            terminal.paste(String.fromCharCode(0x03))
        }
    }

    execute_in_terminal(command: string, id: string = "1") {
        if (command == "<ctrl-c>" || command == "<ctrl+c>")
            return this.interrupt_terminal(id)

        let terminal = this.sessions[id]

        if (terminal) {
            terminal.scrollToBottom()
            terminal.paste(command + "\r")
        }
    }

    execute_in_all_terminals(command: string) {
        for (let id in this.sessions) {
            let terminal = this.sessions[id]

            terminal.scrollToBottom()
            terminal.paste(command + "\r")
        }
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
}

function initialize_terminals() {
    console.log("Initalizing terminals")
    exports.terminals = new Terminals()
}

$(document).ready(() => {
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
            console.log("Loaded fonts okay.")
            initialize_terminals()
        }), () => {
            console.log("Failed to load fonts.")
            initialize_terminals()
        }
    }), () => {
        console.log("Failed to load fonts.")
        initialize_terminals()  
    }
})