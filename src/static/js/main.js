// Wait for the entire document to load before executing the script
document.addEventListener('DOMContentLoaded', function () {
    // Select the mode switch element
    var modeSwitch = document.querySelector('.mode-switch');

    // Initialize dark mode from localStorage
    if (localStorage.getItem('darkMode') === 'true') {
        document.documentElement.classList.add('dark');
        modeSwitch.classList.add('active');
    }

    // Add click event listener to the mode switch to toggle dark mode and active class
    modeSwitch.addEventListener('click', function () { 
        document.documentElement.classList.toggle('dark');
        modeSwitch.classList.toggle('active');

        // Save the dark mode preference in localStorage
        localStorage.setItem('darkMode', document.documentElement.classList.contains('dark'));
    });
    
    // Select the list view and grid view buttons
    var listView = document.querySelector('.list-view');
    var gridView = document.querySelector('.grid-view');
    
    // Select the container that holds the projects
    var projectsList = document.querySelector('.project-boxes');
    
    listView.addEventListener('click', function () {
        gridView.classList.remove('active');
        listView.classList.add('active');
        projectsList.classList.remove('jsGridView');
        projectsList.classList.add('jsListView');
    });
    
    // Add click event to switch to grid view, remove list view class and add grid view class
    gridView.addEventListener('click', function () {
        gridView.classList.add('active');
        listView.classList.remove('active');
        projectsList.classList.remove('jsListView');
        projectsList.classList.add('jsGridView'); 
    });
});

// Select elements related to the file upload area
const dropArea = document.querySelector(".drop_box"),
    button = dropArea.querySelector("button"),
    dragText = dropArea.querySelector("header"),
    input = dropArea.querySelector("input");
let file; // Variable to store the selected file
var filename;

// Trigger file input click when button is clicked
button.onclick = () => {
    input.click();
};


// Handle file selection
input.addEventListener("change", function (e) {
    // Get the file from the input
    var file = e.target.files[0];
    
    // Make sure a file was actually selected
    if (file) {
        // Create a new form element
        var form = document.createElement("form");
        form.action = "/upload";
        form.method = "post";
        form.enctype = "multipart/form-data";

        // Create a new input for the file which will be visible and required
        var fileInput = document.createElement("input");
        fileInput.type = "file";
        fileInput.name = "file";
        fileInput.accept = ".csv";
        fileInput.required = true;
        fileInput.style.display = "none";  // Hide this new input as well

        // Add an event listener to this new input for when a file is selected
        fileInput.addEventListener("change", function () {
            // Submit the form when a new file is selected
            form.submit();
        });

        // Append the file input to the form
        form.appendChild(fileInput);

        // Update the file input with the file the user originally selected
        fileInput.files = e.target.files;

        // Create a submit button for the form
        var submitButton = document.createElement("button");
        submitButton.type = "submit";
        submitButton.className = "btn";
        submitButton.textContent = "Upload";

        // Append the submit button to the form
        form.appendChild(submitButton);

        // Create a label to display the selected file name
        var fileNameLabel = document.createElement("label");
        fileNameLabel.textContent = `Selected file: ${file.name}`;
        form.appendChild(fileNameLabel);

        // Update the drop area with the new form
        dropArea.innerHTML = '';
        dropArea.appendChild(form);

        // Now, simulate a click on the new hidden file input to submit it
        fileInput.click();
    }
});

function updateLowerValue(val) {
    var lowerLabel = document.getElementById('lower-label');
    lowerLabel.innerHTML = val + '%';
    
    // Ensure the lower slider does not cross over the upper slider
    var upperVal = parseInt(document.getElementById('upper').value);
    if (parseInt(val) > upperVal) {
        document.getElementById('lower').value = upperVal;
        lowerLabel.innerHTML = upperVal + '%';
    }
}

function updateUpperValue(val) {
    var upperLabel = document.getElementById('upper-label');
    upperLabel.innerHTML = val + '%';
    
    // Ensure the upper slider does not cross under the lower slider
    var lowerVal = parseInt(document.getElementById('lower').value);
    if (parseInt(val) < lowerVal) {
        document.getElementById('upper').value = lowerVal;
        upperLabel.innerHTML = lowerVal + '%';
    }
}

function updateVisualTrack() {
    var lowerVal = parseInt(document.getElementById('lower').value, 10);
    var upperVal = parseInt(document.getElementById('upper').value, 10);
    var maxVal = parseInt(document.getElementById('lower').max, 10);

    var percentageLower = (lowerVal / maxVal) * 100;
    var percentageUpper = (upperVal / maxVal) * 100;

    var slider = document.querySelector('.multi-range-slider');
    slider.style.setProperty('--range-width', `${percentageUpper - percentageLower}%`);
    slider.style.setProperty('--range-start', `${percentageLower}%`);
}

  // Initialize visual track
updateVisualTrack();

  // Add event listeners
document.getElementById('lower').addEventListener('input', function() {
    updateLowerValue(this.value);
    updateVisualTrack();
});
document.getElementById('upper').addEventListener('input', function() {
    updateUpperValue(this.value);
    updateVisualTrack();
});
