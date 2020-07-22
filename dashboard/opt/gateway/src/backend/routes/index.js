var DEFAULT_PAGE = process.env.DEFAULT_PAGE || '/terminal'

export function index(req, res) {
    res.redirect(DEFAULT_PAGE)
}