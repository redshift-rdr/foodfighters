
function date_select_change(selector, url="/diary/", )
{
    var day = new Date(selector.value).toISOString().split('T')[0];
    window.location.href = url + day;
}

function date_button_change(url="/diary/", mode='minus')
{
    var date_selector = $('#date-select')[0];

    var temp = new Date(date_selector.value);
    if (mode === 'minus')
    {
        temp.setDate(temp.getDate()-1);
    }
    else if (mode === 'add')
    {
        temp.setDate(temp.getDate()+1);
    }
    
    var day = temp.toISOString().split('T')[0];
    window.location.href = url + day;
}

function food_lookup()
{
    var food_input = $('#food_lookup_input')[0];

    // construct the http request
    var url_parts = window.location.href.split('/');
    var mealid = url_parts[4];
    var url = `/addmeal/${mealid}/${food_input.value}`;
    window.location.href = url;
}

$(document).ready(
    function()
    {
        var avatar = $('#avatar')[0];
        if (avatar)
        {
            avatar.src = generateAvatar(avatar.dataset.username.charAt(0).toUpperCase(), "white", "#009578");
        }
    }
);

$(document).on("keypress", "input", function(e){
    if ($(this).attr('id') === 'food_lookup_input') 
    {
        if(e.which == 13)
        {
            food_lookup();
        }
    }
});

function change_foodentry_quantity(uuid, qty)
{

    // construct the http request
    var url = "/api/FoodEntry/" + uuid + "/update";
    var http = new XMLHttpRequest();
    http.onreadystatechange = function()
    {
        // if the request finishes and is successful
        if (http.readyState == 4 && http.status == 200)
        {
            location.reload();
        }
        else if (http.readyState == 4 && http.status != 200)
        {
            // log the error
            console.log(http.responseText);
        }
    };

    // open the request, and set the data type to JSON
    http.open("POST", url);
    http.setRequestHeader("Content-Type", "application/json");

    // send off the request
    http.send(JSON.stringify({ "quantity" : qty }));
}

function edit_food(input, model, attribute)
{
    // grab the task uuid from the checkbox data
    var uuid = input.dataset.uuid;

    // construct the http request
    var url = "/api/" + model + "/" + uuid + "/update";
    var http = new XMLHttpRequest();
    http.onreadystatechange = function()
    {
        // if the request finishes and is successful
        if (http.readyState == 4 && http.status == 200)
        {
            input.classList.add('inputbgsuccess');

            setTimeout( function(){
                input.classList.add('inputbgfade');
                input.classList.remove('inputbgsuccess');
                
            }, 1000);
            //location.reload();

            setTimeout( function() {
                input.classList.remove('inputbgfade');
            }, 1500);
        }
        else if (http.readyState == 4 && http.status != 200)
        {
            // log the error
            console.log(http.responseText);
            input.classList.add('inputbgfail');

            setTimeout( function(){
                input.classList.add('inputbgfade');
                input.classList.remove('inputbgfail');
                
            }, 1000);
            //location.reload();

            setTimeout( function() {
                input.classList.remove('inputbgfade');
            }, 1500);
        }
    };

    // open the request, and set the data type to JSON
    http.open("POST", url);
    http.setRequestHeader("Content-Type", "application/json");

    var input_value = input.value;

    // send off the request
    http.send(JSON.stringify({ [attribute] : input_value }));
}

function edit_food_size(input)
{
    // grab the task uuid from the checkbox data
    var uuid = input.dataset.uuid;

    // construct the http request
    var url = "/api/update_food_size/" + uuid;
    var http = new XMLHttpRequest();
    http.onreadystatechange = function()
    {
        // if the request finishes and is successful
        if (http.readyState == 4 && http.status == 200)
        {
            location.reload();
        }
        else if (http.readyState == 4 && http.status != 200)
        {
            // log the error
            console.log(http.responseText);
        }
    };

    // open the request, and set the data type to JSON
    http.open("POST", url);
    http.setRequestHeader("Content-Type", "application/json");

    // send off the request
    http.send(JSON.stringify({ "serving_size" : input.value }));
}

function edit_nutrition_per100(input)
{
    // grab the task uuid from the checkbox data
    var uuid = input.dataset.uuid;

    // construct the http request
    var url = "/api/update_nutrition/" + uuid;
    var http = new XMLHttpRequest();
    http.onreadystatechange = function()
    {
        // if the request finishes and is successful
        if (http.readyState == 4 && http.status == 200)
        {
            location.reload();
        }
        else if (http.readyState == 4 && http.status != 200)
        {
            // log the error
            console.log(http.responseText);
        }
    };

    // open the request, and set the data type to JSON
    http.open("POST", url);
    http.setRequestHeader("Content-Type", "application/json");

    // send off the request
    http.send(JSON.stringify({ "per_100" : input.value }));
}

function toggle_remove_button(remove_container_id, calories_container_id)
{
    var remove_container = $('.' + remove_container_id);
    var calories_container = $('.' + calories_container_id);

    remove_container.toggle();
    calories_container.toggle();
}

function generateAvatar(text, foregroundColor) {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");

    canvas.width = 125;
    canvas.height = 125;

    // Draw background
    context.fillStyle = "#" + Math.floor(Math.random()*16777215).toString(16);;
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Draw text
    context.font = "bold 100px Assistant";
    context.fillStyle = foregroundColor;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(text, canvas.width / 2, canvas.height / 2 + 5);

    return canvas.toDataURL("image/png");
}

