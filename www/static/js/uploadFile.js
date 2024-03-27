var modal = document.getElementById("uploadFileModal");

function showUploadFileModal() {
    modal.style.display = "block";
}

function closeUploadFileModal() {
    modal.style.display = "none";
}
function uploadFile() {
     closeUploadFileModal(); //closing the modal

     const rank = document.getElementById("rank").value
     const fileUpload = document.getElementById("fileUpload")

     if (fileUpload.files.length === 0) {
        console.log("no files")
        return
     }

     const file = fileUpload.files;

     fetch('/upload', { //http post request.
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({  "rank": rank, "file": file  }),
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