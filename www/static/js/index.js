let selectedDiv = null;

function createNewDiv() {
  var mainContentContainer = document.getElementById('main-content');

  // Create a new div
  var newDiv = document.createElement('div');
  newDiv.classList.add('additional-info');
  newDiv.innerText = 'Additional Information - New Div';
  newDiv.addEventListener('click', function() {
    selectDiv(this);
  });

  // Append the new div to the container
  mainContentContainer.appendChild(newDiv);
}

function selectDiv(div) {
  // Deselect the previously selected div
  if (selectedDiv) {
    selectedDiv.classList.remove('selected');
  }

  // Select the clicked div
  div.classList.add('selected');
  selectedDiv = div;
}

function downloadSelectedDiv() {
  if (selectedDiv) {
    console.log("Selected Div Content:", selectedDiv.innerText);
  } else {
    console.log("No div selected.");
  }
}