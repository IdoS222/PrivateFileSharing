let selectedDiv = null

function selectDiv(div) {
  if (selectedDiv) {
    selectedDiv.classList.remove('selected');
  }

  selectedDiv = div;
  selectedDiv.classList.add('selected'); //We are adding this class so we can change the background color when we click on a div.

  // getting all the data from the div so we can show it in the side bar
  const fileID = selectedDiv.getAttribute('data-fileID');
  const fileName = selectedDiv.getAttribute('data-fileName');
  let pieceSize = selectedDiv.getAttribute('data-pieceSize');
  const numOfPieces = selectedDiv.getAttribute('data-numOfPieces');
  const fileVisibility = selectedDiv.getAttribute('data-fileVisibility');
  let fileOwners = selectedDiv.getAttribute('data-fileOwners');
  let fileUploader = selectedDiv.getAttribute('data-fileUploader');
  const amountOfDownloads = selectedDiv.getAttribute('data-amountOfDownloads');

  pieceSize = pieceSize / 1000000 //converting to MB
  if (pieceSize < 1) {
    pieceSize = 500 + "KB"
  } else {
    pieceSize = pieceSize + "MB"
  }

  fileUploader = JSON.parse(fileUploader) //from json to dict
  dataToShow = fileUploader["firstName"] + " " + fileUploader["lastName"] + ". email:" + fileUploader["email"]
  fileOwners = JSON.parse(fileOwners)
  dataToShowOwners = fileOwners["Peers"]


  //setting all the data in the side bar
  document.getElementById("fileID").innerHTML = "fileID: " + fileID;
  document.getElementById("fileName").innerHTML = "fileName: " + fileName;
  document.getElementById("pieceSize").innerHTML = "pieceSize: " + pieceSize;
  document.getElementById("numOfPieces").innerHTML = "numOfPieces: " + numOfPieces;
  document.getElementById("fileVisibility").innerHTML = "fileVisibility: " + fileVisibility;
  document.getElementById("fileOwners").innerHTML = "fileOwners: " + dataToShowOwners;
  document.getElementById("fileUploader").innerHTML = "fileUploader: " + dataToShow;
  document.getElementById("amountOfDownloads").innerHTML = "amountOfDownloads: " + amountOfDownloads;
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
        'Content-Type': 'application/json', //TODO: WHAT THE FUCK IS A HEADER
      },
      body: JSON.stringify({  fileInfo  }),
    }).then(response => response.json()).then(data => {
        // Handle the response as needed
        if (data.status == "success")
        {
            console.log("yo")
        }
        else
        {

        }
      }).catch(error => console.error('Error during delete:', error));
  }
  else
  {
    //TODO: Implement logic on what happens when we didn't select a div yet
  }
}

