var default_page = process.env.DEFAULT_PAGE || 'dashboard';

function index(req, res) {
    res.redirect(default_page);
}

module.exports = index
