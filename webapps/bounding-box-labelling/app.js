let categories = (dataiku.getWebAppConfig().categories||[]).map(it => ({name: it.from, description: it.to}));
let currentPath;

var mousePressed = false;
var lastX, lastY;
var ctx;
var points;
var annotator;

function drawApp(categories) {
    try {
        dataiku.checkWebAppParameters();
    } catch (e) {
        displayFatalError(e.message + ' Go to settings tab.');
        return;
    }
    annotator = new BBoxAnnotator({
      input_method: 'select',    // Can be one of ['text', 'select', 'fixed']
      labels: categories.map(function(e) { return e.name; }),
      guide: true,
      onchange: function(entries) {
        // Input the text area on change. Use "hidden" input tag unless debugging.
        // <input id="annotation_data" name="annotation_data" type="hidden" />
        // $("#annotation_data").val(JSON.stringify(entries))
        $("#annotation_data").text(JSON.stringify(entries, null, "  "));
      }
    });
    // Initialize the reset button.
    $("#reset_button").click(function(e) {
      annotator.clear_all();
    })
    $("#validate_button").click(function(e) {
      classify();
      next();
    })
    try {
        $('[data-toggle="tooltip"]').tooltip();
    } catch (e) {
        console.warn(e);
    }
    $('#skip').click(next)
    next();
}

function displayFatalError(err) {
    $('#app').hide();
    $('#fatal-error').text(err.message ? err.message : err).show();
}

function next() {
    webappBackend.get('next')
        .then(updateProgress)
        .catch(displayFatalError);
}

function drawItem(bbox) {
    if (!currentPath || !currentPath.length) {
        $('#app').html('<div id="done"><div>The End</div><p>All the images were labelled (or skipped, refresh to see the skipped ones)</p></div>')
    } else {
        webappBackend.get('get-image-base64', {path: currentPath}).then(function(resp) {
            let contentType = 'image/jpg';
            annotator.update_image(`data:${contentType};base64,${resp.data}`, bbox);
            $('#comment').val('');
        });
    }
}

function classify() {
    const comment = $('#comment').val()
    webappBackend.get('classify', {path: currentPath, comment: $('#comment').val(), bbox: $('#annotation_data').val()}, updateProgress);
}

function updateProgress(resp) {
    currentPath = resp.nextPath;
    $('#remaining').text(resp.remaining);
    drawItem(resp.bbox);
    $('#app').show();
}

drawApp(categories);