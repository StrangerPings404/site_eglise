document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('file', document.getElementById('fileInput').files[0]);
    formData.append('caption', e.target.elements.caption.value);

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    if (response.ok) {
        location.reload(); // Recharge la galerie
    } else {
        alert("Erreur lors de l'upload");
    }
});