function input_create() {       // creates new input fields
    const fields = document.getElementById("inputFields");
    const wrapper = document.createElement("div");
    const appliance = document.createElement("input");
    const breaker = document.createElement("br")
    appliance.setAttribute("type", "text");
    appliance.setAttribute("class", "input")
    appliance.setAttribute("placeholder", "Enter appliance name")
    appliance.classList.add("input-field");
    const energy = document.createElement("input");
    energy.setAttribute("type", "number");
    energy.setAttribute("placeholder", "Energy Usage")
    energy.setAttribute("class", "energy1 input")
    energy.setAttribute("name", "energy1")
    energy.setAttribute("step", 0.01)
    energy.setAttribute("min", 0)
    energy.classList.add("input-field");
    wrapper.appendChild(appliance);
    wrapper.appendChild(energy);
    wrapper.appendChild(breaker)
    wrapper.appendChild(breaker);
    fields.appendChild(wrapper);
}

function no_meter() {       // disables inputs which arent used
    var x = document.getElementById("inputFields");
    if (x.style.display === "none") {
        x.style.display = "block";
        document.getElementById("energy0").disabled = true;
        var inputs = document.querySelectorAll("input.energy1");
        inputs.forEach(input => input.disabled =false);
    } else {
        x.style.display = "none";
        document.getElementById("energy0").disabled = false;
        var inputs = document.querySelectorAll("input.energy1");
        inputs.forEach(input => input.disabled = true);
    }
}