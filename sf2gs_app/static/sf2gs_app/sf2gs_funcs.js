function startTimePicker() {
    Timepicker.showPicker({
        time: document.querySelector("#start_time").value,
        onSubmit: (selected) => {
            document.querySelector("#start_time").value = selected.formatted();
        }
    })
}
function endTimePicker() {
    Timepicker.showPicker({
        time: document.querySelector("#end_time").value,
        onSubmit: (selected) => {
            document.querySelector("#end_time").value = selected.formatted();
        }
    })
}
function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length == 2) return parts.pop().split(";").shift();
}
function updateDB(){
    console.log("UPDATE!")
    document.getElementById("loading").style.display = "block";
    fetch("{% url 'updatedb' %}")
    .then(response => response.json())
    .then(data =>   {
                    console.log(data);
                    document.getElementById("loading").style.display = "none";
                    }
        );
}
function download(){
    //# 1. Collect all parameters from user selections:
    let start_date=[]
    let end_date=[]
    for (const datepicker of datepickers) {
        start_date.push(datepicker.getStartDate());
        end_date.push(datepicker.getEndDate());
    }
    const start_time= document.querySelector("#start_time").value
    const end_time= document.querySelector("#end_time").value
    time0 = new Date();
    document.getElementById("loading").style.display = "block";
    const vble_to_plot = document.querySelector('input[name="js_or_js_vpd"]:checked').value;
    const vble_to_plot2 = document.querySelector('input[name="vpd_or_par"]:checked').value;
    const stations_selected=document.querySelector("#sel_station").selectedOptions
    const trees_selected=document.querySelector("#sel_tree").selectedOptions
    const thermocouple_depths_selected=document.querySelector("#sel_depth").selectedOptions
    vpd_range=[parseFloat(vpdSlider.getValue().split(",")[0]),parseFloat(vpdSlider.getValue().split(",")[1])]
    par_range=[parseFloat(parSlider.getValue().split(",")[0]),parseFloat(parSlider.getValue().split(",")[1])]
    js_range=[parseFloat(jsSlider.getValue().split(",")[0]),parseFloat(jsSlider.getValue().split(",")[1])]
    if (stations_selected.length==0 || trees_selected.length==0 || thermocouple_depths_selected.length==0 ) {
        document.getElementById("loading").style.display = "none";
        alert("You must select a station, a tree and a thermocouple depth to Plot!")
        return            
    }
    const station=stations_selected[0].value
    const tree=trees_selected[0].value
    const thermocouple_depth=thermocouple_depths_selected[0].value
    const csrftoken = getCookie('csrftoken');

    //# 2. Call to download_view fucntion on views.py passing all the parameters selected by the user
    fetch("{% url 'download-sf2gs' %}", {
        method: "POST",
        headers: {
            'X-CSRFToken': csrftoken  // Incluir el token CSRF en el encabezado
        },
        body: JSON.stringify(
            { "start_date" : start_date,
            "end_date" : end_date,
            "start_time": start_time,
            "end_time": end_time,
            "station" : station,
            "tree": tree,
            "thermocouple_depth":thermocouple_depth,
            "vble_to_plot":vble_to_plot,
            "vpd_range":vpd_range,
            "par_range":par_range,
            "js_range":js_range
            },
        )
    })
    .then(
        response=>response.blob()
    )
    .then(blob => {
        document.getElementById("loading").style.display = "none";
        // Create a temporal link to download the file
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = "data.csv";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error("Error uploading files:", error);
    });
}

function plot(){
    //# 1. Collect all parameters from user selections:
    let start_date=[]
    let end_date=[]
    for (const datepicker of datepickers) {
        start_date.push(datepicker.getStartDate());
        end_date.push(datepicker.getEndDate());
    }
    const start_time= document.querySelector("#start_time").value
    const end_time= document.querySelector("#end_time").value  
    document.getElementById("loading").style.display = "block";
    const vble_to_plot = document.querySelector('input[name="js_or_js_vpd"]:checked').value;
    const vble_to_plot2 = document.querySelector('input[name="vpd_or_par"]:checked').value;
    const stations_selected=document.querySelector("#sel_station").selectedOptions
    const trees_selected=document.querySelector("#sel_tree").selectedOptions
    const thermocouple_depths_selected=document.querySelector("#sel_depth").selectedOptions
    if (stations_selected.length==0 || trees_selected.length==0 || thermocouple_depths_selected.length==0 ) {
        document.getElementById("loading").style.display = "none";
        alert("You must select a station, a tree and a thermocouple depth to Plot!")
        return            
    }
    const station=stations_selected[0].value
    const tree=trees_selected[0].value
    const thermocouple_depth=thermocouple_depths_selected[0].value
    const csrftoken = getCookie('csrftoken');
    vpd_range=[parseFloat(vpdSlider.getValue().split(",")[0]),parseFloat(vpdSlider.getValue().split(",")[1])]
    par_range=[parseFloat(parSlider.getValue().split(",")[0]),parseFloat(parSlider.getValue().split(",")[1])]
    js_range=[parseFloat(jsSlider.getValue().split(",")[0]),parseFloat(jsSlider.getValue().split(",")[1])]
    
    //# 2. Call to plot_view fucntion on views.py passing all the parameters selected by the user
    fetch(plotUrl, {
        method: "POST",
        headers: {
            'X-CSRFToken': csrftoken  // Incluir el token CSRF en el encabezado
        },
        body: JSON.stringify(
            { "start_date" : start_date,
            "end_date" : end_date,
            "start_time": start_time,
            "end_time": end_time,
            "station" : station,
            "tree": tree,
            "thermocouple_depth":thermocouple_depth,
            "vble_to_plot":vble_to_plot,
            "vble_to_plot2":vble_to_plot2,
            "vpd_range":vpd_range,
            "par_range":par_range,
            "js_range":js_range
            },
        )
    })
    .then(
        response=>response.json()
    )
    .then(data => {
        const chart =JSON.parse(data["chart"])
        Plotly.newPlot('chart1', chart)
        const chart2 =JSON.parse(data["chart2"])
        Plotly.newPlot('chart2', chart2)        
        document.getElementById("loading").style.display = "none";
    })
    .catch(error => {
        console.error("Error uploading files:", error);
    });
}   

function initializeDatepickers(def_start_Date,def_end_Date){        
    const datepicker=new Litepicker({
        element: document.getElementById('js_daterange'),
        singleMode: false,
        tooltipText: {
            one: 'night',
            other: 'nights'
        },
        tooltipNumber: (totalDays) => {
            return totalDays - 1;
        }
    })
        
    datepicker.setDateRange(def_start_Date, def_end_Date);
    const daterangeContainer = document.querySelector('.daterange_container');
    const addrange=document.querySelector('#add_range')//.onclick =add_range;
    
    datepickers.push(datepicker)
    addrange.addEventListener('click', () => {
        count_ranges++
        const newDaterange = document.createElement('div');
        newDaterange.classList.add('js_daterange');

        const heading = document.createElement('h2');
        heading.textContent = `Date range ${count_ranges}`;

        const input = document.createElement('input');
        input.setAttribute('type', 'text');
        input.classList.add('date-input');

        newDaterange.appendChild(heading);
        newDaterange.appendChild(input);

        daterangeContainer.appendChild(newDaterange);//, addrange);

        const newDatepicker = new Litepicker({
            element: input,
            singleMode: false,
            tooltipText: {
                one: 'night',
                other: 'nights'
            },
            tooltipNumber: (totalDays) => {
                return totalDays - 1;
            }
        });
        datepickers.push(newDatepicker);
        input.addEventListener('change', (event) => {
            console.log('Nuevo valor:', event.target.value);
        });
    });
    const removerange=document.querySelector('#remove_range')//.onclick =add_range;
    removerange.addEventListener('click', () => {
        const lastrange = daterangeContainer.lastElementChild;
        if (lastrange) {
            daterangeContainer.removeChild(lastrange);
            datepickers.pop();
        }
    })
    return datepicker, datepickers
}

function initializeOptions(){
    document.querySelector('#Js_vpd').checked=true;
            document.querySelector('#vpd_vs_time').checked=true;
            
            document.querySelector('#startTime_button').onclick = startTimePicker;
            document.querySelector('#endTime_button').onclick = endTimePicker;

            document.querySelector('#download_button').onclick = download;
            document.querySelector('#plot_button').onclick = plot;//(start_date,end_date)};//,station=station,tree=tree,thermocouple_depth=depth)};
            document.querySelector('#update_button').onclick = updateDB;
            
            const vpdarr=arrayRange(0,10,0.1)
            const pararr=arrayRange(0,1500,1)
            const jsarr=arrayRange(0,300,1)

            vpdSlider = new rSlider({
                target: '#vpdSlider',
                values: vpdarr,
                range: true,
                tooltip: true,
                scale: false,
                labels: false,
                set: [0.0, 10.0]
            });
            parSlider = new rSlider({
                target: '#parSlider',
                values: pararr,
                range: true,
                tooltip: true,
                scale: false,
                labels: false,
                set: [0.0, 1500.0]
            });
            jsSlider = new rSlider({
                target: '#jsSlider',
                values: jsarr,
                range: true,
                tooltip: true,
                scale: false,
                labels: false,
                set: [0.0, 150.0]
            });
            document.querySelectorAll('.rs-tooltip')[0].style.opacity='50%'
}

