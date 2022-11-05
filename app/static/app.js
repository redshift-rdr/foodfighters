
function date_select_change(selector)
{
    var day = new Date(selector.value).toISOString().split('T')[0];
    window.location.href = "/diary/" + day;
}

function date_button_change(mode='minus')
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
    window.location.href = "/diary/" + day;
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


$(document).on("keypress", "input", function(e){
    if ($(this).attr('id') === 'food_lookup_input') 
    {
        if(e.which == 13)
        {
            food_lookup();
        }
    }
});
