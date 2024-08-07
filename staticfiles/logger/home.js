const maxLength = 40;

var webSocket;
var chart;
var scatterChart;
var dynamicChart;
var datasets = [];
var dps = [];
var pieChart;
var dynamicSVMChart;
var svmDps = [];

function connectWebSocket() {
    webSocket = new WebSocket("ws://" + window.location.host + "/ws/logger/receive/");
    webSocket.onmessage = function (e) {
        var data = JSON.parse(e.data);
        // 수신된 데이터 확인
        console.log("Received data-js:", data);

        updateChart(data["x_test_twelve_sec"]);
        updateDynamicPPGChart(data["ppg_data"]);
        updateScatter(data["predictions"]);
        updatePieChart(data["acc_predictions"]);
        updateDynamicSVMChart(data["svm_acc_data"]);
    };
    webSocket.onclose = function (e) {
        setTimeout(connectWebSocket, 1000);
    };
}

function updateChart(x_test_twelve_sec) {
    datasets = [];
    x_test_twelve_sec.forEach((subArray, index) => {
        var chartData = [];
        subArray.forEach((value, idx) => {
            chartData.push({ x: idx, y: value });
        });

        datasets.push({
            type: "line",
            name: "" + (index + 1),
            showInLegend: true,
            markerSize: 0,
            dataPoints: chartData,
            color: getRandomColor()
        });
    });

    if (!chart) {
        chart = new CanvasJS.Chart("chartContainer", {
            title: {
                text: "Normalized PPG Data"
            },
            axisX: {
                title: "Sample Index"
            },
            axisY: {
                title: "Signal Value",
                minimum: 0,
                maximum: 1
            },
            data: datasets
        });
    } else {
        chart.options.data = datasets;
    }

    chart.render();
}

function updateScatter(predictions) {
    // 로그 추가 - 업데이트할 산점도 데이터 확인
    console.log("Updating scatter chart with predictions:", predictions);
    dataPoints = predictions.map((y, x) => ({
        x: x,
        y: y,
        color: y <= 0.75 ? "blue" : "red" // 색상 조건 설정
    }));


    if (!scatterChart) {
        scatterChart = new CanvasJS.Chart("scatterChartContainer", {
            animationEnabled: true,
            zoomEnabled: true,
            title: {
                text: "Predictions Scatter Plot"
            },
            axisX: {
                title: "Index",
                minimum: 0,
                maximum: predictions.length
            },
            axisY: {
                title: "Prediction",
                valueFormatString: "#0.00",
                minimum: 0,
                maximum: 1,
                interval: 0.25
            },
            data: [{
                type: "scatter",
                toolTipContent: "<b>Index: </b>{x}<br/><b>Prediction: </b>{y}",
                dataPoints: dataPoints
            }]
        });
    } else {
        scatterChart.options.data[0].dataPoints = dataPoints;
        scatterChart.options.axisX.minimum = 0;
        scatterChart.options.axisX.maximum = predictions.length;
        scatterChart.options.axisY = {
            title: "Prediction",
            minimum: 0,
            maximum: 1,
            interval: 0.25,
            valueFormatString: "#0.00"
        };
    }

    scatterChart.render();
}

function updatePieChart(acc_predictions) {
    // 로그 추가 - 업데이트할 파이 차트 데이터 확인
    console.log("Updating pie chart with acc_predictions:", acc_predictions);

    // acc_predictions 배열의 값들을 카운트합니다.
    const counts = {0: 0, 1: 0, 2: 0, 3: 0};
    acc_predictions.forEach(prediction => {
        counts[prediction] = (counts[prediction] || 0) + 1;
    });

    // 파이 차트에 사용할 데이터 포인트를 생성
    const dataPoints = Object.keys(counts).map(key => {
        let label;
        switch (key) {
            case '0':
                label = 'walk';
                break;
            case '1':
                label = 'run';
                break;
            case '2':
                label = 'danger';
                break;
            case '3':
                label = 'desk work';
                break;
            default:
                label = `Class ${key}`;
        }
        return { y: counts[key], label: label };
    });

    // 로그 추가 - 생성된 데이터 포인트 확인
    console.log("Generated data points for pie chart:", dataPoints);

    if (!pieChart) {
        pieChart = new CanvasJS.Chart("pieChartContainer", {
            animationEnabled: true,
            title: {
                text: "ACC Predictions Distribution"
            },
            data: [{
                type: "pie",
                startAngle: 240,
                yValueFormatString: "##0\"\"",
                indexLabel: "{label} {y}",
                dataPoints: dataPoints
            }]
        });
    } else {
        pieChart.options.data[0].dataPoints = dataPoints;
    }

    pieChart.render();

    // 카운트된 라벨을 텍스트로 표시
    const labelCountsContainer = document.getElementById("labelCounts");
    labelCountsContainer.innerHTML = ""; // 기존 내용을 초기화

    for (const [key, count] of Object.entries(counts)) {
        if (count > 0) {
            let label;
            switch (key) {
                case '0':
                    label = 'walk';
                    break;
                case '1':
                    label = 'run';
                    break;
                case '2':
                    label = 'danger';
                    break;
                case '3':
                    label = 'desk work';
                    break;
                default:
                    label = `Class ${key}`;
            }
            const labelCountElement = document.createElement("p");
            labelCountElement.textContent = label;
            labelCountsContainer.appendChild(labelCountElement);
        }
    }
}

function getRandomColor() {
    var letters = '0123456789ABCDEF';
    var color = '#';
    for (var i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

var ppgQueue = [];

function updateDynamicPPGChart(ppg_data) {
    ppgQueue = ppgQueue.concat(ppg_data);

    while (ppgQueue.length > 300) {
        ppgQueue.shift();
    }

    dps = ppgQueue.map((value, index) => ({ x: index, y: value }));

    if (!dynamicChart) {
        dynamicChart = new CanvasJS.Chart("dynamicChartContainer", {
            exportEnabled: true,
            title :{
                text: "Dynamic PPG Chart"
            },
            data: [{
                type: "spline",
                markerSize: 0,
                dataPoints: dps
            }]
        });
    } else {
        dynamicChart.options.data[0].dataPoints = dps;
    }

    dynamicChart.render();
}

var svmAccQueue = [];

function updateDynamicSVMChart(svm_acc_data) {
    svmAccQueue = svmAccQueue.concat(svm_acc_data);

    while (svmAccQueue.length > 300) {
        svmAccQueue.shift();
    }

    svmDps = svmAccQueue.map((value, index) => ({ x: index, y: value }));

    if (!dynamicSVMChart) {
        dynamicSVMChart = new CanvasJS.Chart("dynamicSVMChartContainer", {
            exportEnabled: true,
            title: {
                text: "Dynamic IMU Chart"
            },
            data: [{
                type: "spline",
                markerSize: 0,
                dataPoints: svmDps
            }]
        });
    } else {
        dynamicSVMChart.options.data[0].dataPoints = svmDps;
    }

    dynamicSVMChart.render();
}

function init() {
    connectWebSocket();
}

init();
