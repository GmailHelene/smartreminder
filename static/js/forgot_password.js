document.addEventListener('DOMContentLoaded', function() {
    // Add forgot password modal HTML if it doesn't exist
    if (!document.getElementById('forgot-password-modal')) {
        const modalHTML = `
            <div id="forgot-password-modal" class="modal" style="display: none;">
                <div class="modal-content">
                    <span class="close">&times;</span>
                    <h2>Tilbakestill passord</h2>
                    <form id="forgot-password-form">
                        <div class="form-group">
                            <label for="reset-email">E-post adresse:</label>
                            <input type="email" id="reset-email" name="email" required>
                        </div>
                        <button type="submit" class="btn btn-primary">Send tilbakestillingslenke</button>
                    </form>
                    <div id="reset-message" class="message" style="display: none;"></div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    // Handle forgot password link click
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('forgot-password-modal').style.display = 'block';
        });
    }

    // Handle modal close
    const closeModal = document.querySelector('#forgot-password-modal .close');
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            document.getElementById('forgot-password-modal').style.display = 'none';
        });
    }

    // Handle form submission
    const forgotPasswordForm = document.getElementById('forgot-password-form');
    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('reset-email').value;
            
            fetch('/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({email: email})
            })
            .then(response => response.json())
            .then(data => {
                const messageDiv = document.getElementById('reset-message');
                messageDiv.style.display = 'block';
                messageDiv.textContent = data.message;
                messageDiv.className = data.success ? 'message success' : 'message error';
                
                if (data.success) {
                    setTimeout(() => {
                        document.getElementById('forgot-password-modal').style.display = 'none';
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const messageDiv = document.getElementById('reset-message');
                messageDiv.style.display = 'block';
                messageDiv.textContent = 'Det oppstod en feil. Prøv igjen senere.';
                messageDiv.className = 'message error';
            });
        });
    }
});
