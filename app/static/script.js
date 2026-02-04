document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('recommendation-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    const resultDiv = document.getElementById('result');
    const successDiv = resultDiv.querySelector('.result-success');
    const errorDiv = resultDiv.querySelector('.result-error');
    const resultAlbum = document.getElementById('result-album');
    const errorMessage = document.getElementById('error-message');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Show loading state
        submitBtn.disabled = true;
        btnText.hidden = true;
        btnLoading.hidden = false;
        resultDiv.hidden = true;

        const formData = {
            name: form.name.value.trim(),
            album_url: form.album_url.value.trim(),
            context: form.context.value.trim(),
            access_code: form.access_code.value.trim()
        };

        try {
            const response = await fetch('/api/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                // Success
                successDiv.hidden = false;
                errorDiv.hidden = true;
                resultAlbum.textContent = data.album_title && data.artist_name
                    ? `${data.album_title} by ${data.artist_name}`
                    : 'Album added to queue';

                // Clear form except access code
                form.name.value = '';
                form.album_url.value = '';
                form.context.value = '';
            } else {
                // Error
                successDiv.hidden = true;
                errorDiv.hidden = false;
                errorMessage.textContent = data.detail || 'Something went wrong. Please try again.';
            }
        } catch (err) {
            successDiv.hidden = true;
            errorDiv.hidden = false;
            errorMessage.textContent = 'Network error. Please check your connection and try again.';
        } finally {
            // Reset button
            submitBtn.disabled = false;
            btnText.hidden = false;
            btnLoading.hidden = true;
            resultDiv.hidden = false;
        }
    });
});
