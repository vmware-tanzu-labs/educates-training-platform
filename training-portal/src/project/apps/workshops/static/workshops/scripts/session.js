

function check_readiness(session_url, restart_url, startup_timeout) {
  start_time_ms = Date.now();

  startup_progress_panel = document.getElementById("startup-progress-panel");
  startup_progress_bar = document.getElementById("startup-progress-bar");

  if (startup_timeout) {
    startup_progress_panel.style.visibility = "visible";
  }

  function poll_session() {
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

  function check_readiness() {
    $.ajax({
      type: 'GET',
      url: session_url + "/session/poll",
      cache: false,
      success: function(data, textStatus, xhr) {
        if (xhr.status == 200) {
          $("#session").attr("src", session_url+"/");
          setTimeout(function(){$("#startup-cover-panel").hide();}, 500)
          setTimeout(function(){poll_session();}, 15000);
        }
        else {
          setTimeout(function(){retry_readiness();}, 1000);
        }
      },
      error: function() {
        setTimeout(function(){retry_readiness();}, 1000);
      }
    });
  }

  function retry_readiness() {
    if (startup_timeout) {
      current_time_ms = Date.now();

      percentage = Math.floor((100*(current_time_ms-start_time_ms)/1000) / startup_timeout)

      startup_progress_bar.style.width = percentage + "%";

      if ((current_time_ms - start_time_ms)/ 1000 > startup_timeout) {
        window.top.location.href = restart_url;

        return
      }
    }

    check_readiness();
  }

  check_readiness();
}
