$(document).ready(function() {
    $.each([$('code.language-execute')], function() {
        if (window.location !== window.parent.location) {
            this.parent().prepend('<span class="execute-glyph fas fa-running" aria-hidden="true"></span>');
            this.parent().click(function(event) {
                if (event.shiftKey) {
                    $(this).find('.execute-glyph').removeClass('text-danger');
                    $(this).find('.execute-glyph').addClass('text-success');
                    handle_copy(event);
                }
                else {
                    $(this).find('.execute-glyph').removeClass('text-success');
                    $(this).find('.execute-glyph').addClass('text-danger');
                    handle_execute(event, 1);
                }
                selectElementText(this);
            });
        } else {
            this.parent().prepend('<span class="copy-glyph fas fa-copy" aria-hidden="true"></span>');
            this.parent().click(function(event) {
                $(this).find('.copy-glyph').addClass('text-success');
                handle_copy(event);
                selectElementText(this);
            });
        }
    });

    $.each([$('code.language-execute-1')], function() {
        if (window.location !== window.parent.location) {
            this.parent().prepend('<span class="execute-glyph fas fa-running" aria-hidden="true"><sup><sup>1</sup></sup></span>');
            this.parent().click(function(event) {
                if (event.shiftKey) {
                    $(this).find('.execute-glyph').removeClass('text-danger');
                    $(this).find('.execute-glyph').addClass('text-success');
                    handle_copy(event);
                }
                else {
                    $(this).find('.execute-glyph').removeClass('text-success');
                    $(this).find('.execute-glyph').addClass('text-danger');
                    handle_execute(event, 1);
                }
                selectElementText(this);
            });
        } else {
            this.parent().prepend('<span class="copy-glyph fas fa-copy" aria-hidden="true"></span>');
            this.parent().click(function(event) {
                $(this).find('.copy-glyph').addClass('text-success');
                handle_copy(event);
                selectElementText(this);
            });
        }
    });

    $.each([$('code.language-execute-2')], function() {
        if (window.location !== window.parent.location) {
            this.parent().prepend('<span class="execute-glyph fas fa-running" aria-hidden="true"><sup><sup>2</sup></sup></span>');
            this.parent().click(function(event) {
                if (event.shiftKey) {
                    $(this).find('.execute-glyph').removeClass('text-danger');
                    $(this).find('.execute-glyph').addClass('text-success');
                    handle_copy(event);
                }
                else {
                    $(this).find('.execute-glyph').removeClass('text-success');
                    $(this).find('.execute-glyph').addClass('text-danger');
                    handle_execute(event, 2);
                }
                selectElementText(this);
            });
        } else {
            this.parent().prepend('<span class="copy-glyph fas fa-copy" aria-hidden="true"></span>');
            this.parent().click(function(event) {
                $(this).find('.copy-glyph').addClass('text-success');
                handle_copy(event);
                selectElementText(this);
            });
        }
    });

    $.each([$('code.language-execute-3')], function() {
        if (window.location !== window.parent.location) {
            this.parent().prepend('<span class="execute-glyph fas fa-running" aria-hidden="true"><sup><sup>3</sup></sup></span>');
            this.parent().click(function(event) {
                if (event.shiftKey) {
                    $(this).find('.execute-glyph').removeClass('text-danger');
                    $(this).find('.execute-glyph').addClass('text-success');
                    handle_copy(event);
                }
                else {
                    $(this).find('.execute-glyph').removeClass('text-success');
                    $(this).find('.execute-glyph').addClass('text-danger');
                    handle_execute(event, 3);
                }
                selectElementText(this);
            });
        } else {
            this.parent().prepend('<span class="copy-glyph fas fa-copy" aria-hidden="true"></span>');
            this.parent().click(function(event) {
                $(this).find('.copy-glyph').addClass('text-success');
                handle_copy(event);
                selectElementText(this);
            });
        }
    });

    $.each([$('code.language-copy'), $('code.language-copypaste')], function() {
        this.parent().prepend('<span class="copy-glyph fas fa-copy" aria-hidden="true"></span>');
        this.parent().click(function(event) {
            $(this).find('.copy-glyph').addClass('text-success');
            handle_copy(event);
            selectElementText(this);
        });
    });

    $.each([$('code.language-copy-and-edit')], function() {
        this.parent().prepend('</span><span class="copy-and-edit-glyph fas fa-user-edit" aria-hidden="true"></span>');
        this.parent().click(function(event) {
            $(this).find('.copy-and-edit-glyph').addClass('text-warning');
            handle_copy(event);
            selectElementText(this);
        });
    });
});
