let categories = (dataiku.getWebAppConfig().categories || []).map(it => ({name: it.from, description: it.to}));
let currentSID;


var mousePressed = false;
var lastX, lastY;
var ctx;
var points;

function initCanvas(elementId, image_data) {
    canvas = document.getElementById(elementId);
    ctx = canvas.getContext("2d");
    // Clear the canvas
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    points = [];

    // Draw the image
    var image = new Image();
    image.onload = function () {
        canvas.width = image.width;
        canvas.height = image.height;
        ctx.drawImage(image, 0, 0);
    };
    image.src = image_data;

    elementId = '#' + elementId;

    $(elementId).mousedown(function (e) {
        mousePressed = true;
        draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
        points.push([e.pageX - $(this).offset().left, e.pageY - $(this).offset().top])
    });

    $(elementId).mousemove(function (e) {
        if (mousePressed) {
            draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
            points.push([e.pageX - $(this).offset().left, e.pageY - $(this).offset().top])
        }
    });

    $(elementId).mouseup(function (e) {
        mousePressed = false;
    });
    $(elementId).mouseleave(function (e) {
        mousePressed = false;
    });
}

function draw(x, y, isDown) {
    if (isDown) {
        ctx.beginPath();
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 1;
        ctx.lineJoin = "round";
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.closePath();
        ctx.stroke();
    }
    lastX = x;
    lastY = y;
}


function drawApp(categories) {
    try {
        dataiku.checkWebAppParameters();
    } catch (e) {
        displayFatalError(e.message + ' Go to settings tab.');
        return;
    }
    drawCategories(categories);
    try {
        $('[data-toggle="tooltip"]').tooltip();
    } catch (e) {
        console.warn(e);
    }
    $('#skip').click(skip);
    next();
}

function displayFatalError(err) {
    $('#app').hide();
    $('#fatal-error').text(err.message ? err.message : err).show();
}

function drawCategory(category) {
    var buttonHtml;
    if (category.description) {
        // button with description tooltip
        buttonHtml = `<button id="cat_${category.name}" class="btn btn-default category-button" data-toggle="tooltip" data-placement="bottom" title="${category.name}"><div class="ratio"></div>${category.description}&nbsp;<i class="icon-info-sign"></i></button>`
    } else {
        // simple button
        buttonHtml = `<button id="cat_${category.name}" class="btn btn-default category-button">${category.name}<div class="ratio"></div></button>`
    }
    const button = $(buttonHtml)
    $('#category-buttons').append(button);
}

function drawCategories(categories) {
    $('#category-buttons').empty();
    categories.forEach(drawCategory);
    $('#category-buttons button').each((idx, button) => {
        $(button).click(() => {
            classify(categories[idx].name);
            next()
        })
    });
}

function setCategoryCount(name, count, total) {
    $(`#cat_${name}>.ratio`).width('' + (100 * count / total) + '%')
}

function next() {
    webappBackend.get('sample')
        .then(updateProgress)
        .catch(displayFatalError);
}

function skip() {
    webappBackend.get('skip')
        .then(updateProgress)
        .catch(displayFatalError);
}

function drawItem(imgData) {
    //TODO: use a better condition
    if (!imgData) {
        $('#app').html('<div id="done"><div>The End</div><p>All the images were labelled (or skipped, refresh to see the skipped ones)</p></div>')
    } else {
        let contentType = 'image/jpg';
        initCanvas("item-to-classify-canvas", `data:${contentType};base64,${imgData}`);
        $('#comment').val('');
    }
}

function classify(category) {
    const comment = $('#comment').val()
    webappBackend.post('classify', {
        sid: currentSID,
        comment: $('#comment').val(),
        category: category,
        points: String(points)
    }, updateProgress);
}

function updateProgress(resp) {
    currentSID = resp.sid;
    $('#total').text(resp.total);
    $('#labelled').text(resp.labelled);
    $('#skipped').text(resp.skipped);
    $.each(resp.byCategory, (name, count) => setCategoryCount(name, count, resp.total))
    drawItem(resp.data);
    $('#app').show();
}

drawApp(categories);