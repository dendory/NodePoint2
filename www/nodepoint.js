function init()
{
}

function show_form($name)
{
	var divsToHide = document.getElementsByClassName("np_form");
	for(var i = 0; i < divsToHide.length; i++)
	{
		divsToHide[i].style.display = "none";
	}
	document.getElementById($name).style.display = "block";
}

function parse_output()
{
	var iframe = document.getElementById('output_frame');
	var raw = iframe.contentWindow.document.body.innerText;
	if(raw != null && raw != undefined && raw != "")
	{
		var results = JSON.parse(raw);
		if(results["authkey"] != undefined)
		{
		    var authkeys = document.getElementsByClassName("authkey");
		    for(var i = 0; i < authkeys.length; i++)
		    {
        		authkeys[i].value = results["authkey"]
		    }
            var buttons = document.getElementsByClassName("cmd");
            for(var i = 0; i < buttons.length; i++)
            {
				buttons[i].className = "list-group-item list-group-item-success cmd";
			}
		}
		if(results["code"] == "OK")
		{
			document.getElementById("output_msg").className = "alert alert-success";
			document.getElementById("output_msg").innerHTML = results["message"];
		}
		else
		{
			document.getElementById("output_msg").className = "alert alert-danger";
			document.getElementById("output_msg").innerHTML = results["message"];
		}
	}
}
