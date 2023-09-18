import * as express from "express"
import * as http from "http"
import * as WebSocket from "ws"

import { v4 as uuidv4 } from "uuid"

enum MessagesPacketType {
    HELLO,
    PING,
    MESSAGE,
}

interface MessagesPacket {
    type: MessagesPacketType
    id: string
    args?: any
}

interface HelloPacketArgs {
}

interface MessagePacketArgs {
    name: string
    args: any
}

class MessagesChannel {
    private sockets: WebSocket[] = []

    constructor(public readonly id: string) {
        console.log("Initializing messages channel", id)
    }

    private send_message(ws: WebSocket, type: MessagesPacketType, args?: any) {
        if (ws.readyState !== WebSocket.OPEN)
            return

        let packet = {
            type: type,
            id: this.id
        }

        if (args !== undefined)
            packet["args"] = args

        let message = JSON.stringify(packet)

        ws.send(message)
    }

    broadcast_message(type: MessagesPacketType, args?: any) {
        let packet = {
            type: type,
            id: this.id
        }

        if (args !== undefined)
            packet["args"] = args

        let message = JSON.stringify(packet)

        this.sockets.forEach((ws) => {
            if (ws.readyState === WebSocket.OPEN)
                ws.send(message)
        })
    }

    close_connections() {
        this.sockets.forEach((ws) => { ws.close() })
    }

    cleanup_connection(ws: WebSocket) {
        let index = this.sockets.indexOf(ws)
        if (index != -1)
            this.sockets.splice(index, 1)
    }

    handle_message(ws: WebSocket, packet: MessagesPacket) {
        switch (packet.type) {
            case MessagesPacketType.HELLO: {
                let args: HelloPacketArgs = packet.args

                if (this.sockets.indexOf(ws) == -1) {
                    console.log("Adding messages channel", this.id)

                    this.sockets.push(ws)
                }

                break
            }
        }
    }
}

class SessionManager {
    static instance: SessionManager

    id: string = uuidv4()

    private socket_server: WebSocket.Server

    private sessions = new Map<String, MessagesChannel>()

    private constructor() {
        this.socket_server = new WebSocket.Server({ noServer: true })

        this.configure_handlers()
    }

    static get_instance(): SessionManager {
        if (!SessionManager.instance)
            SessionManager.instance = new SessionManager()

        return SessionManager.instance
    }

    private configure_handlers() {
        this.socket_server.on("connection", (ws: WebSocket) => {
            ws.on("message", (message: string) => {
                let packet: MessagesPacket = JSON.parse(message)
                let session: MessagesChannel = this.retrieve_session(packet.id)

                session.handle_message(ws, packet)
            })

            ws.on("close", () => {
                this.cleanup_connection(ws)
            })
        })
    }

    private retrieve_session(id: string): MessagesChannel {
        let session: MessagesChannel = this.sessions.get(id)

        if (!session) {
            session = new MessagesChannel(id)
            this.sessions.set(id, session)
        }

        return session
    }

    private cleanup_connection(ws: WebSocket) {
        this.sessions.forEach((session: MessagesChannel) => {
            session.cleanup_connection(ws)
        })
    }

    handle_upgrade(req, socket, head) {
        this.socket_server.handleUpgrade(req, socket, head, (ws) => {
            this.socket_server.emit('connection', ws, req)
        })
    }

    broadcast_message(data: any) {
        this.sessions.forEach((session: MessagesChannel) => {
            session.broadcast_message(MessagesPacketType.MESSAGE, data)
        })
    }

    close_all_sessions() {
        this.sessions.forEach((session: MessagesChannel) => {
            session.close_connections()
        })
    }
}

export class MessagesServer {
    id: string

    constructor() {
        this.id = SessionManager.get_instance().id
    }

    session_manager() {
        return SessionManager.get_instance()
    }

    is_enabled() {
        return true
    }

    broadcast_message(data: any) {
        SessionManager.get_instance().broadcast_message(data)
    }

    close_all_sessions() {
        SessionManager.get_instance().close_all_sessions()
    }
}

export const messages = new MessagesServer()

export function setup_messages(app: express.Application, server: http.Server, token: string = null) {
    app.use("/message/broadcast$", express.json());

    async function messages_broadcast(req, res, next) {
        let data = req.body

        messages.broadcast_message(data)

        res.status(200).send('OK')
    }

    if (token) {
        app.post("/message/broadcast", async function (req, res, next) {
            let request_token = req.query.token

            if (!request_token || request_token != token)
                return next()

            return await messages_broadcast(req, res, next)
        })
    }
    else {
        app.post("/message/broadcast", messages_broadcast)
    }
}
