var mousePressed = false;
var lastX, lastY;
var ctx;

function initCanvas(elementId, image) {
    ctx = document.getElementById(elementId).getContext("2d");
    alert(image);
    // Clear the canvas
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

    // Draw the image
    ctx.drawImage(image, 0, 0);
    
    $(elementId).mousedown(function (e) {
        mousePressed = true;
        draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
    });

    $(elementId).mousemove(function (e) {
        if (mousePressed) {
            draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
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
    lastX = x; lastY = y;
}