const fileElements = document.querySelectorAll('.file-info');
let selectedDiv = null

function selectDiv(div) {
  if (selectedDiv) {
    selectedDiv.classList.remove('selected');
  }

  selectedDiv = div;
  selectedDiv.classList.add('selected');

}

function downloadSelectedFile() {
  if (selectedDiv) {
    const fileInfo = selectedDiv.querySelector('p').textContent;
    console.log(fileInfo)

    // Send file information to a Python script using Fetch API
    fetch('/download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ fileInfo }),
    })
      .then(response => response.json())
      .then(data => {
        console.log('Download response from Python script:', data);
        // Handle the response as needed
      })
      .catch(error => console.error('Error during download:', error));
  } else {
    console.log("No file selected");
  }
}

fileElements.forEach((fileElement) => {
  fileElement.addEventListener('click', function() {
    selectDiv(this);
  });
});