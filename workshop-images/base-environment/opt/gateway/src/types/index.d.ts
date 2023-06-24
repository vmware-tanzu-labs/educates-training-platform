export {};

declare module 'express-session' {
    interface SessionData {
        identity: {
            owner: string
            staff: string
            user: string
        }
        access_token: string
        refresh_token: string
        started: string
        page_hits: number
    }
}
