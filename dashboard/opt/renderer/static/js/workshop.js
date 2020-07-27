var eduk8s = {
    execute_in_terminal: function(text, terminal=1) {
        if (parent && parent.eduk8s)
            parent.eduk8s.terminals.execute_in_terminal(text, terminal);
    },

    execute_in_all_terminals: function(text) {
        if (parent && parent.eduk8s)
            parent.eduk8s.terminals.execute_in_all_terminals(text);
    },

    reload_terminals: function() {
        if (parent && parent.eduk8s)
            parent.eduk8s.terminals.reconnect_all_terminals();
    },

    expose_dashboard: function(name) {
        if (parent && parent.eduk8s)
            parent.eduk8s.dashboard.expose_dashboard(name);
    },

    reload_dashboard: function() {
        if (parent && parent.eduk8s)
            parent.eduk8s.dashboard.reload_dashboard(name);
    },

    collapse_workshop: function() {
        if (parent && parent.eduk8s)
            parent.eduk8s.dashboard.collapse_workshop();
    },

    reload_workshop: function() {
        if (parent && parent.eduk8s)
            parent.eduk8s.dashboard.reload_workshop();
    },

    finished_workshop: function() {
        if (parent && parent.eduk8s)
            parent.eduk8s.dashboard.finished_workshop()
    },

    preview_image: function(src, title) {
        if (parent && parent.eduk8s)
            parent.eduk8s.dashboard.preview_image(src, title)
    },
};


function handle_execute(event, terminal) {
    var text = $(event.target).contents().not($('.execute-glyph')).text().trim();
    if (terminal == '*') {
        eduk8s.execute_in_all_terminals(text);
    } else {
        eduk8s.execute_in_terminal(text, terminal);
    }
}

function handle_copy(event) {
    var text = $(event.target).text().trim();
    var element = $('<textarea>').appendTo('body').val(text).select();
    document.execCommand('copy');
    element.remove();
}

function handle_console_link(event) {
    event.preventDefault();
    parent.open_link_in_console(event.target.href);
}

function handle_slides_link(event) {
    event.preventDefault();
    parent.open_link_in_slides(event.target.href);
}

function handle_terminal_link(event) {
    event.preventDefault();
    parent.bring_terminal_to_front();
}

function open_image_zoom_popup(src, title) {
    $('#image-zoom')[0].src = src;
    $('#image-zoom-title')[0].innerHTML = title;
    $('#image-zoom-popup').modal('show');
}

function handle_image_zoom(event) {
    if (parent && parent.eduk8s) {
        eduk8s.preview_image(event.target.src, event.target.alt);
    }
    else {
        open_image_zoom_popup(event.target.src, event.target.alt);
    }
}

function selectElementText(el, win) {
    win = win || window;
    var doc = win.document, sel, range;
    if (win.getSelection && doc.createRange) {
        sel = win.getSelection();
        range = doc.createRange();
        range.selectNodeContents(el);
        sel.removeAllRanges();
        sel.addRange(range);
    } else if (doc.body.createTextRange) {
        range = doc.body.createTextRange();
        range.moveToElementText(el);
        range.select();
    }
}

$(document).ready(function() {
    /*
    $('section.page-content a').each(function() {
        function normalize(path){
            path = Array.prototype.join.apply(arguments,['/'])
            var sPath;
            while (sPath!==path) {
                sPath = n(path);
                path = n(sPath);
            }
            function n(s){return s.replace(/\/+/g,'/').replace(/\w+\/+\.\./g,'')}
            return path.replace(/^\//,'').replace(/\/$/,'');
        }

        var base_url = (typeof workshop_base_url === 'undefined') ? '' : workshop_base_url;

        var console_url = '/' + normalize(base_url + '/../console');
        var slides_url = '/' + normalize(base_url + '/../slides');
        var terminal_url = '/' + normalize(base_url + '/../terminal');

        if (location.hostname === this.hostname || !this.hostname.length) {
            if (this.pathname.startsWith(console_url)) {
                $(this).click(function(event) {
                    handle_console_link(event);
                });
            }
            else if (this.pathname.startsWith(slides_url)) {
                $(this).click(function(event) {
                    handle_slides_link(event);
                });
            }
            else if (this.pathname.startsWith(terminal_url)) {
                if (this.pathname == terminal_url) {
                    $(this).click(function(event) {
                        handle_terminal_link(event);
                    });
                }
                else {
                    $(this).attr('target','_blank');
                }
            }
        }
        else {
            $(this).attr('target','_blank');
        }
    });
    */

    $('section.page-content a').each(function() {
        if (!(location.hostname === this.hostname || !this.hostname.length)) {
            $(this).attr('target','_blank');
        }
    });

    $('section.page-content img').each(function() {
        $(this).click(function(event) {
            handle_image_zoom(event);
        });
    });

    $('.modal-wide').on('show.bs.modal', function() {
      var height = $(window).height() - 200;
      $(this).find('.modal-body').css('max-height', height);
    });
});
