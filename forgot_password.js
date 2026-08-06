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
            <style>
                .modal {
                    position: fixed;
                    z-index: 1000;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0,0,0,0.5);
                }
                .modal-content {
                    background-color: white;
                    margin: 15% auto;
                    padding: 20px;
                    border-radius: 8px;
                    width: 90%;
                    max-width: 400px;
                    position: relative;
                }
                .close {
                    position: absolute;
                    right: 15px;
                    top: 15px;
                    font-size: 28px;
                    font-weight: bold;
                    cursor: pointer;
                    color: #aaa;
                }
                .close:hover {
                    color: #000;
                }
                .form-group {
                    margin-bottom: 15px;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }
                .form-group input {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                .btn {
                    width: 100%;
                    padding: 10px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }
                .btn:hover {
                    background-color: #0056b3;
                }
                .message {
                    padding: 10px;
                    margin: 10px 0;
                    border-radius: 4px;
                    text-align: center;
                }
                .message.success {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }
                .message.error {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }
            </style>
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
            // Clear form and message
            document.getElementById('reset-email').value = '';
            const messageDiv = document.getElementById('reset-message');
            messageDiv.style.display = 'none';
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('forgot-password-modal');
        if (e.target === modal) {
            modal.style.display = 'none';
            // Clear form and message
            document.getElementById('reset-email').value = '';
            const messageDiv = document.getElementById('reset-message');
            messageDiv.style.display = 'none';
        }
    });

    // Handle form submission
    const forgotPasswordForm = document.getElementById('forgot-password-form');
    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = document.getElementById('reset-email').value;
            const submitBtn = this.querySelector('button[type="submit"]');
            
            // Disable button during request
            submitBtn.disabled = true;
            submitBtn.textContent = 'Sender...';
            
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
                        // Clear form
                        document.getElementById('reset-email').value = '';
                        messageDiv.style.display = 'none';
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const messageDiv = document.getElementById('reset-message');
                messageDiv.style.display = 'block';
                messageDiv.textContent = 'Det oppstod en feil. Prøv igjen senere.';
                messageDiv.className = 'message error';
            })
            .finally(() => {
                // Re-enable button
                submitBtn.disabled = false;
                submitBtn.textContent = 'Send tilbakestillingslenke';
            });
        });
    }
});
