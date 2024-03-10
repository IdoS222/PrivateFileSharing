let selectedDiv = null

function selectDiv(div) {
  if (selectedDiv) {
    selectedDiv.classList.remove('selected');
  }

  selectedDiv = div;
  selectedDiv.classList.add('selected'); //We are adding this class so we can change the background color when we click on a div.

}

function downloadSelectedFile() {
  if (selectedDiv) {
    const fileID = selectedDiv.getAttribute('data-fileID');
    const fileName = selectedDiv.getAttribute('data-fileName');
    const pieceSize = selectedDiv.getAttribute('data-pieceSize');
    const numOfPieces = selectedDiv.getAttribute('data-numOfPieces');


    const fileInfo = {
        "fileID":fileID,
        "fileName":fileName,
        "pieceSize":pieceSize,
        "numOfPieces":numOfPieces
   };

    fetch('/download', { //sending a post request to the download route.
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({  fileInfo  }),
    })
      .then(response => response.json())
      .then(data => {
        // Handle the response as needed
      })
      .catch(error => console.error('Error during download:', error));
  } 
  else 
  {
    //TODO: Implement logic on what happens when we didn't select a div yet
  }
}

function deleteSelectedDiv() {
  if (selectedDiv) {
    const fileID = selectedDiv.getAttribute('data-fileID');
    const fileName = selectedDiv.getAttribute('data-fileName');

    const fileInfo = {
        "fileID":fileID,
        "fileName":fileName,
   };

    fetch('/delete', { //sending a post request to the download route.
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({  fileInfo  }),
    })
      .then(response => response.json())
      .then(data => {
        // Handle the response as needed
      })
      .catch(error => console.error('Error during delete:', error));
  }
  else
  {
    //TODO: Implement logic on what happens when we didn't select a div yet
  }
}


