document.getElementById('faqForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        url: document.getElementById('url').value,
        platform: document.getElementById('platform').value,
        language: document.getElementById('language').value,
        faq_count: document.getElementById('faq_count').value
    };
    
    // Validate URL
    if (!isValidUrl(formData.url)) {
        showError('Please enter a valid URL starting with http:// or https://');
        return;
    }
    
    // Show loading, hide error
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    document.getElementById('generateBtn').disabled = true;
    document.getElementById('generateBtn').innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Processing...';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Start polling for status
            pollStatus(data.job_id);
        } else {
            throw new Error(data.error || 'Failed to start generation process');
        }
        
    } catch (error) {
        showError(error.message);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('generateBtn').disabled = false;
        document.getElementById('generateBtn').innerHTML = '<i class="bi bi-gear-fill me-2"></i>Generate FAQs';
    }
});

async function pollStatus(jobId) {
    try {
        const response = await fetch(`/status/${jobId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
            // Show success message before redirecting
            updateProgress(100, 'Generation complete! Redirecting...');
            setTimeout(() => {
                window.location.href = `/result/${jobId}`;
            }, 1000);
        } else if (data.status === 'failed') {
            throw new Error(data.error || 'FAQ generation process failed');
        } else {
            // Update progress
            updateProgress(data.progress, data.message);
            
            // Continue polling with exponential backoff
            const delay = Math.min(3000, 1000 + (data.progress * 20));
            setTimeout(() => pollStatus(jobId), delay);
        }
        
    } catch (error) {
        showError(error.message);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('generateBtn').disabled = false;
        document.getElementById('generateBtn').innerHTML = '<i class="bi bi-gear-fill me-2"></i>Generate FAQs';
    }
}

function updateProgress(percent, message) {
    const progressBar = document.querySelector('.progress-bar');
    const statusMessage = document.getElementById('statusMessage');
    
    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute('aria-valuenow', percent);
    statusMessage.textContent = message;
    
    // Update button text during processing
    if (percent < 100) {
        document.getElementById('generateBtn').innerHTML = `<i class="bi bi-hourglass-split me-2"></i>Processing`;
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');
    
    errorMessage.textContent = message;
    errorDiv.style.display = 'block';
    
    // Scroll to error message
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Add keyboard shortcut (Enter to submit form)
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        const focused = document.activeElement;
        if (focused.tagName !== 'TEXTAREA') {
            e.preventDefault();
            document.getElementById('faqForm').dispatchEvent(new Event('submit'));
        }
    }
});