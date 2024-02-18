let selectedDiv = null;

function createNewDiv(fileID, fileName, fileSize, pieceSize, amountOfPieces, fileVisibility, fileOwners, fileUploader) {
  var mainContentContainer = document.getElementById('main-content');

  // Create a new div
  var newDiv = document.createElement('div');
  newDiv.classList.add('additional-info');
  newDiv.innerText = fileName + "-" + fileUploader;
  newDiv.addEventListener('click', function() {
    toggleSelectDiv(this);
  });

  // Append the new div to the container
  mainContentContainer.appendChild(newDiv);
}

function toggleSelectDiv(div) {
  if (div === selectedDiv) {
    // Deselect the div if it's already selected
    div.classList.remove('selected');
    selectedDiv = null;
  } else {
    // Deselect the previously selected div
    if (selectedDiv) {
      selectedDiv.classList.remove('selected');
    }

    // Select the clicked div
    div.classList.add('selected');
    selectedDiv = div;
  }

  // Enable or disable the download button
  updateDownloadButtonState();
}

function updateDownloadButtonState() {
  var downloadButton = document.getElementById('download-btn');

  if (selectedDiv) {
    downloadButton.classList.add('enabled');
    downloadButton.disabled = false;
  } else {
    downloadButton.classList.remove('enabled');
    downloadButton.disabled = true;
  }
}

function downloadSelectedDiv() {
  if (selectedDiv) {
    console.log("Selected Div Content:", selectedDiv.innerText);
  } else {
    console.log("No div selected.");
  }
}