var modal = document.getElementById("uploadFileModal");

function showUploadFileModal() {
    modal.style.display = "block";
}

function closeUploadFileModal() {
    modal.style.display = "none";
}
function uploadFile(rank) {
     closeUploadFileModal(); //closing the modal
     fetch('/upload', { //sending a post request to the download route.
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({  "rank": rank  }),
    })
      .then(response => response.json())
      .then(data => {
        // Handle the response as needed
      })
      .catch(error => console.error('Error during delete:', error));
}

window.onclick = function(event) { //code from W3 school
  if (event.target == modal) {
    closeUploadFileModal()
  }
}