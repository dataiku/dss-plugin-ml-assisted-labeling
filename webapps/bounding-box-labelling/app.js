let categories = (dataiku.getWebAppConfig().categories || []).map(it => ({name: it.from, description: it.to}));
let currentId;

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
        labels: categories.map(function (e) {
            return e.name;
        }),
        guide: true,
        onchange: function (entries) {
            // Input the text area on change. Use "hidden" input tag unless debugging.
            // <input id="annotation_data" name="annotation_data" type="hidden" />
            // $("#annotation_data").val(JSON.stringify(entries))
            $("#annotation_data").text(JSON.stringify(entries, null, "  "));
        }
    });
    // Initialize the reset button.
    $("#reset_button").click(function (e) {
        annotator.clear_all();
    })
    $("#validate_button").click(function (e) {
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

function drawItem(resp) {
    if (!currentId || !currentId.length) {
        $('#app').html('<div id="done"><div>The End</div><p>All the images were labelled (or skipped, refresh to see the skipped ones)</p></div>')
    } else {
        let contentType = 'image/jpg';
        annotator.update_image(`data:${contentType};base64,${resp.data.img}`, resp.data.bbox);
        $('#comment').val('');
    }
}

function classify() {
    webappBackend.post('classify', {
        sid: currentId,
        comment: $('#comment > textarea').val(),
        bbox: $('#annotation_data').val()
    }, updateProgress)
}

function updateProgress(resp) {
    currentId = resp.sid;
    $('#remaining').text(resp.remaining);
    drawItem(resp);
    $('#app').show();
}

drawApp(categories);