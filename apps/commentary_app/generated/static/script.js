document.getElementById('uploadForm').onsubmit = async function(event) {
    event.preventDefault(); // Prevent the default form submission behavior
    const formData = new FormData(this); // Create a FormData object from the form

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData // Send the form data to the server
        });

        const result = await response.json(); // Parse the JSON response
        const commentaryDiv = document.getElementById('commentary'); // Get the commentary div

        if (response.ok) {
            commentaryDiv.innerText = result.commentary; // Display the commentary
            commentaryDiv.style.display = 'block'; // Show the commentary div
        } else {
            commentaryDiv.innerText = result.error; // Display the error message
            commentaryDiv.style.display = 'block'; // Show the commentary div
        }
    } catch (error) {
        console.error('Error:', error); // Log any errors that occur during the fetch
        const commentaryDiv = document.getElementById('commentary');
        commentaryDiv.innerText = 'An unexpected error occurred. Please try again.'; // Display a generic error message
        commentaryDiv.style.display = 'block'; // Show the commentary div
    }
};