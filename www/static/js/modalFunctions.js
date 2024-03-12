function showModal() {
    var modal = document.getElementsByClassName("modal")[0];
    console.log(modal)
    modal.style.display = "block";
}

function closeModal() {
    var modal = document.getElementsByClassName("modal")[0];
    modal.style.display = "none";
}
function uploadFile(rank) {
     closeModal(); //closing the modal
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