
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