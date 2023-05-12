'use strict';


const serverURL = 'SERVER_URL'
let tempJWT = null;
let wsJWT = null;
let tm;

const streamOutput = (text, color) => {
    document.getElementById('stream-output').innerHTML += `<span style="color: ${color}">${text}</span><br>`;
};



function getAuth() {
    const jwt_req = new XMLHttpRequest();
    const url = serverURL + '/authorize';
    jwt_req.open("POST", url);
    jwt_req.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    jwt_req.setRequestHeader('Authorization', 'Bearer ' + tempJWT)
    jwt_req.responseType = "text";
    jwt_req.send();

    jwt_req.onload = function () {
        if (jwt_req.status == 200) {
            wsJWT = jwt_req.response
            connect()
        } else {
            streamOutput('Connection refused:' + jwt_req.status, 'red');
        }
    };
}

function requestReport(reportPath) {
    const report_req = new XMLHttpRequest();
    const url = serverURL + '/report';
    report_req.open("POST", url);
    report_req.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    report_req.setRequestHeader('Authorization', 'Bearer ' + tempJWT)
    report_req.responseType = "blob";

    report_req.send(reportPath);

    report_req.onload = function () {
        if (report_req.status == 200) {
            // NOTE: Trigger Download
            let report = new Blob([this.response], { type: 'text/csv' });

            let dummyAnchor = document.createElement("a");
            dummyAnchor.style = "display: none";
            document.body.appendChild(dummyAnchor);

            let downloadURL = window.URL.createObjectURL(report);
            dummyAnchor.href = downloadURL;
            dummyAnchor.download = `${reportPath.split(/[0-9]-/)[1]}`;
            dummyAnchor.click();
            window.URL.revokeObjectURL(downloadURL);


            streamOutput('< File Request Complete! >', 'green');

        } else {

            streamOutput('Connection refused:' + jwt_req.status, 'red');
        }
    };
}




function connect() {

    const queryParams = `?temp_access_token=${wsJWT}`

    const socket = new WebSocket('wss://' + location.host + '/stream' + queryParams);

    function ping() {
        socket.send('__ping__');
        tm = setTimeout(function () {

            /// ---connection closed ///


        }, 5000);
    }

    function pong() {
        clearTimeout(tm);
    }

    socket.onopen = function () {
        setInterval(ping, 5000);

        streamOutput('< Connection established with streaming server! >', 'green');
        streamOutput('< Shadow Clone Server Up! >', 'green');

    };

    socket.onclose = function (e) {
        streamOutput('< Socket is closed. Reconnect will be attempted in 1 second. >' + e.reason, 'orange');
        setTimeout(function () {
            connect();
        }, 1000);
    };

    socket.onmessage = function (e) {

        if (e.data == '__pong__') {
            pong();
        }

        else if (e.data.startsWith("REPORT_PATH=")) {
            streamOutput('< Requesting Generated Report! >', 'blue');
            streamOutput('< CONNECTION WITH SERVER WILL RESET >', 'orange');

            requestReport(e.data)

        }
        else { streamOutput('>>> ' + e.data, 'grey'); }
    };

    document.getElementById('json-form').onsubmit = (e) => {
        e.preventDefault();
        let jsonField = document.getElementById('jsonField');
        let obj = e.target.jsonField.value
        obj = JSON.parse(obj)
        const blob = new Blob([JSON.stringify(obj)], { type: 'application/json' });
        socket.send(blob);
        e.target.jsonField.value = '';
        streamOutput('< Request Data Sent! >', 'blue');
    };
}


document.getElementById('jwt-form').onsubmit = (e) => {
    e.preventDefault();
    try {
        tempJWT = e.target.jwtField.value;
        getAuth();
        e.target.jwtField.value = '';
        streamOutput('< Connection request sent! >', 'blue');
    }
    catch (error) {
        streamOutput('>>> ' + error, 'red');
        e.target.jwtField.value = '';
    }
}


