function poll_session(session_url) {
  $.ajax({
    type: 'GET',
    url: session_url + "/session/poll",
    cache: false,
    success: function(data, textStatus, xhr) {
      setTimeout(function(){poll_session(session_url);}, 15000);
    },
    error: function() {
      setTimeout(function(){poll_session(session_url);}, 15000);
    }
  });
}

function check_readiness(session_url) {
  $.ajax({
    type: 'GET',
    url: session_url + "/session/poll",
    cache: false,
    success: function(data, textStatus, xhr) {
      if (xhr.status == 200) {
        $("#session").attr("src", session_url+"/");
        $("#startup-cover-panel").hide();
        setTimeout(function(){poll_session(session_url);}, 15000);
      }
      else {
        setTimeout(function(){check_readiness(session_url);}, 1000);
      }
    },
    error: function() {
      setTimeout(function(){check_readiness(session_url);}, 1000);
    }
  });
}
