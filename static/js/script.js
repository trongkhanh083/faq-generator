document.getElementById('faqForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = {
        url: document.getElementById('url').value,
        platform: document.getElementById('platform').value,
        language: document.getElementById('language').value,
        faq_count: document.getElementById('faq_count').value
    };
    
    // Show loading, hide error
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    document.getElementById('generateBtn').disabled = true;
    
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
            throw new Error(data.error || 'Failed to start generation');
        }
        
    } catch (error) {
        showError(error.message);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('generateBtn').disabled = false;
    }
});

async function pollStatus(jobId) {
    try {
        const response = await fetch(`/status/${jobId}`);
        const data = await response.json();
        
        if (data.status === 'completed') {
            // Redirect to result page
            window.location.href = `/result/${jobId}`;
        } else if (data.status === 'failed') {
            throw new Error(data.error || 'Generation failed');
        } else {
            // Update progress
            updateProgress(data.progress, data.message);
            
            // Continue polling
            setTimeout(() => pollStatus(jobId), 2000);
        }
        
    } catch (error) {
        showError(error.message);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('generateBtn').disabled = false;
    }
}

function updateProgress(percent, message) {
    const progressBar = document.querySelector('.progress-bar');
    const statusMessage = document.getElementById('statusMessage');
    
    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute('aria-valuenow', percent);
    statusMessage.textContent = message;
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}