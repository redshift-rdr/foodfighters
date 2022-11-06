let video = document.querySelector("#video");

video.setAttribute('playsinline', '');
video.setAttribute('autoplay', '');
video.setAttribute('muted', '');

/* Setting up the constraint */
var facingMode = "environment"; // Can be 'user' or 'environment' to access back or front camera (NEAT!)
var constraints = {
  audio: false,
  video: {
   facingMode: facingMode,
    width: { ideal: 4096 },
    height: { ideal: 2160 }
  }
};

/* Stream it to video element */
navigator.mediaDevices.getUserMedia(constraints).then(function success(stream) {
  video.srcObject = stream;
});

setInterval(send_image, 1000);

function send_image() 
{
	var canvas = document.createElement("canvas");
	canvas.width = video.videoWidth;
	canvas.height = video.videoHeight;
	canvas.getContext('2d').drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
	
	//document.querySelector("#shot").appendChild(canvas);
   	canvas.toBlob((blob) => {
		var url = '/scan_barcode';
		var http = new XMLHttpRequest();
		var meal_id = document.getElementById('meal_id').value;
		http.onreadystatechange = function()
		{
			if (http.readyState == 4 && http.status == 200)
			{
				window.location.href = `/barcode/search/${meal_id}/${http.responseText}`;
			}
		};

		http.open("POST", url);
		http.send(blob);
		// const resp = fetch('/scan_barcode',
		// {
		// 	method: 'POST',
		// 	body: blob
		// }).then(response => response.text())
	    // .then((response) => {
		// 	window.location.href = '/barcode/search/' + response;
		// })
	});	
}