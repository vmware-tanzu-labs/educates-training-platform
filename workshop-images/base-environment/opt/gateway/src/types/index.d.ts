export {};

declare module 'express-session' {
    interface SessionData {
        identity: {
            owner: string
            staff: string
            user: string
        }
        token: string
        started: string
        page_hits: number
    }
}