/**
 * reCAPTCHA Enterprise Demo JavaScript
 * 
 * This file contains utility functions for working with reCAPTCHA Enterprise
 * in the demo application.
 */

class RecaptchaDemo {
    constructor(siteKey, options = {}) {
        this.siteKey = siteKey;
        this.options = {
            minScore: 0.5,
            expectedAction: 'submit',
            ...options
        };
        this.isReady = false;
        this.init();
    }

    init() {
        if (!this.siteKey) {
            console.error('reCAPTCHA site key not provided');
            return;
        }

        // Wait for reCAPTCHA to be ready
        if (typeof grecaptcha !== 'undefined' && grecaptcha.enterprise) {
            grecaptcha.enterprise.ready(() => {
                this.isReady = true;
                console.log('reCAPTCHA Enterprise ready');
                this.onReady();
            });
        } else {
            console.error('reCAPTCHA Enterprise not loaded');
        }
    }

    onReady() {
        // Override this method in subclasses or pass as option
        if (this.options.onReady) {
            this.options.onReady();
        }
    }

    async execute(action = this.options.expectedAction) {
        if (!this.isReady) {
            throw new Error('reCAPTCHA Enterprise not ready');
        }

        try {
            const token = await grecaptcha.enterprise.execute(this.siteKey, { action });
            return token;
        } catch (error) {
            console.error('reCAPTCHA execution failed:', error);
            throw error;
        }
    }

    async submitForm(form, endpoint, options = {}) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        try {
            // Disable submit button
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            // Execute reCAPTCHA
            const token = await this.execute();

            // Prepare form data
            const formData = new FormData(form);
            formData.append('recaptcha_token', token);

            // Submit form
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    ...options.headers
                }
            });

            const data = await response.json();

            if (response.ok) {
                return { success: true, data };
            } else {
                throw new Error(data.message || 'Form submission failed');
            }

        } catch (error) {
            console.error('Form submission error:', error);
            throw error;
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    showMessage(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of the main container
        const main = document.querySelector('main .container');
        if (main) {
            main.insertBefore(alert, main.firstChild);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Contact form handler
class ContactFormHandler extends RecaptchaDemo {
    constructor(siteKey, options = {}) {
        super(siteKey, options);
        this.form = document.getElementById('contact-form');
        this.bindEvents();
    }

    bindEvents() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }
    }

    async handleSubmit() {
        try {
            // Execute reCAPTCHA first
            const token = await this.execute();
            
            // Add the token to the form
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'recaptcha_token';
            tokenInput.value = token;
            this.form.appendChild(tokenInput);
            
            // Submit the form normally (let Django handle it)
            this.form.submit();
            
        } catch (error) {
            this.showMessage(
                `reCAPTCHA failed: ${error.message}`,
                'danger'
            );
        }
    }
}

// Registration form handler
class RegistrationFormHandler extends RecaptchaDemo {
    constructor(siteKey, options = {}) {
        super(siteKey, options);
        this.form = document.getElementById('registration-form');
        this.bindEvents();
    }

    bindEvents() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }
    }

    async handleSubmit() {
        try {
            const result = await this.submitForm(this.form, '/api/accounts/register/');
            
            if (result.success) {
                this.showMessage(
                    `Registration successful! reCAPTCHA Score: ${result.data.recaptcha_score}`,
                    'success'
                );
                this.form.reset();
            }
        } catch (error) {
            this.showMessage(
                `Registration failed: ${error.message}`,
                'danger'
            );
        }
    }
}

// Export for use in other scripts
window.RecaptchaDemo = RecaptchaDemo;
window.ContactFormHandler = ContactFormHandler;
window.RegistrationFormHandler = RegistrationFormHandler;
