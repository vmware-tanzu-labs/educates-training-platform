var DEFAULT_PAGE = process.env.DEFAULT_PAGE || '/terminal/'

function index(req, res) {
    res.redirect(DEFAULT_PAGE)
}

exports.default = index

module.exports = exports.default