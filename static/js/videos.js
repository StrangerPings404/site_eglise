// Ajout d'une nouvelle vidéo
document.getElementById('videoForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = document.getElementById('youtubeUrl').value;
    const youtubeId = extractYoutubeId(url); // Fonction pour extraire l'ID
    
    if (!youtubeId) {
        alert("Lien YouTube invalide !");
        return;
    }

    const response = await fetch('/add_video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            youtube_id: youtubeId,
            title: document.getElementById('videoTitle').value,
            description: document.getElementById('videoDesc').value
        })
    });

    if (response.ok) {
        location.reload();
    } else {
        alert("Erreur lors de l'ajout");
    }
});

// Extraire l'ID YouTube depuis une URL
function extractYoutubeId(url) {
    const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|youtu\.be\/)([^"&?\/\s]{11})/;
    const match = url.match(regex);
    return match ? match[1] : null;
}