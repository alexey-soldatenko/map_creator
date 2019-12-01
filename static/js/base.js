function getRequest () {
    if(XMLHttpRequest) return new XMLHttpRequest();
    else if(ActiveXObject) {
        try { return new ActiveXObject('Msxml2.XMLHTTP') }
        catch(e) {
            try { return new ActiveXObject('Microsoft.XMLHTTP') }
            catch(e) { return null; }
        }
    }
}

function send_user_data_to_server(ev, element, url) {
    if (is_increased_map != null){
        var rect = element.getBoundingClientRect();
        var x = ev.clientX - rect.left;
        var y = ev.clientY - rect.top;
        var send_data = "?zoom=2&x=" + x + "&y=" + y;
        var xhr = getRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4) {
                if (xhr.status == 200) {
                    var data = JSON.parse(xhr.responseText);
                    if (data.status == 'ok'){
                        element.innerHTML = data.svg_content;
                        lat = data.x;
                        lon = data.y;
                        current_zoom = data.zoom;
                    }
                    else {
                        console.log(data.message);
                    }
                }
            }
        };
        xhr.open('POST', url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(JSON.stringify({'zoom': current_zoom, 'x': lat, 'y': lon, 'offset_x': x, 'offset_y': y, 'is_increased_map': is_increased_map}));
        console.log("send");
    } 
}

var is_increased_map = null;

var svg_container = document.getElementById("svg_container");
svg_container.addEventListener("dblclick", function(ev){
    send_user_data_to_server(ev, element=svg_container, url="/zoom");
});

var increase_button = document.getElementById("increase_zoom");
var decrease_button = document.getElementById("decrease_zoom");

increase_button.addEventListener("click", function(ev){
    is_increased_map = true;
    increase_button.classList.add("checked_map_settings");
    decrease_button.classList.remove("checked_map_settings");
    svg_container.style.cursor = "crosshair";
});
decrease_button.addEventListener("click", function(ev){
    is_increased_map = false;
    decrease_button.classList.add("checked_map_settings");
    increase_button.classList.remove("checked_map_settings");
    svg_container.style.cursor = "crosshair";
});
