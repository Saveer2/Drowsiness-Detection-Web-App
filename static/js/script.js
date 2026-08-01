function updateStatus(){

fetch("/status")

.then(response=>response.json())

.then(data=>{

document.getElementById("message").innerHTML=data.status;

document.getElementById("ear").innerHTML=data.ear;

document.getElementById("mar").innerHTML=data.mar;

if(data.status==="Drowsiness Detected"){

document.getElementById("alert").innerHTML="🚨 Wake Up!";

}

else if(data.status==="Yawning"){

document.getElementById("alert").innerHTML="⚠ Take a Break";

}

else{

document.getElementById("alert").innerHTML="✅ Normal";

}

});

}

setInterval(updateStatus,300);