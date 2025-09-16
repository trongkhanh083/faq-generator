from flask import Flask, request, jsonify, render_template
import os
import threading
import uuid
import traceback
from datetime import datetime

from pipeline import run_pipeline
from database import db

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB

# Configuration for production
app.config['DEBUG'] = False

# results = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_faq():
    try:
        data = request.get_json()

        # Validate input
        if not data or 'url' not in data or 'platform' not in data:
            return jsonify({'error': 'URL and platform are required'}), 400

        url = data['url']
        platform = data['platform']
        language = data.get('language', 'en')
        faq_count = data.get('faq_count', 10)
        
        # Validate platform
        valid_platforms = ["fb", "ig", "x", "df"]
        if platform not in valid_platforms:
            return jsonify({'error': f"Invalid platform '{platform}'. Choose from {valid_platforms}."}), 400
        
        # Validate FAQ count
        try:
            faq_count = int(faq_count)
            if faq_count < 1 or faq_count > 50:
                return jsonify({'error': 'FAQ count must be between 1 and 50'}), 400
        except ValueError:
            return jsonify({'error': 'FAQ count must be an integer'}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Store initial result
        initial_result = {
            'status': 'Processing...',
            'message': 'Starting FAQ generation...',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'data': None,
            'error': None
        }
        db.store_result(job_id, initial_result)

        # Start processing in a background thread
        thread = threading.Thread(
            target=process_faq_generation,
            args=(job_id, url, platform, language, faq_count)
        )
        thread.daemon = True
        thread.start()

        return jsonify({'job_id': job_id, 'status': 'processing'})
    
    except Exception as e:
        return jsonify({'error': f"Server error: {str(e)}"}), 500
    
@app.route('/status/<job_id>')
def get_status(job_id):
    result = db.get_result(job_id)
    if not result:
        return jsonify({'error': 'Invalid job ID'}), 404
    
    return jsonify(result)

@app.route('/result/<job_id>')
def get_result(job_id):
    result = db.get_result(job_id)
    if not result:
        return jsonify({'error': 'Invalid job ID'}), 404
    
    if result['status'] == 'completed':
        return render_template('result.html', result=result)
    else:
        return jsonify(result)
    
def process_faq_generation(job_id, url, platform, language, faq_count):
    try:
        # Update progress
        db.store_result(job_id, {
            'status': 'processing',
            'progress': 25,
            'message': 'Downloading page content...',
            'created_at': datetime.now().isoformat(),
            'data': None,
            'error': None
        })

        # Run the pipeline
        out_file = f"output_{job_id}_faq.md"
        success = run_pipeline(
            url, 
            plf=platform,
            out_file=out_file,
            language=language, 
            faq_count=faq_count
        )

        if success:
            # Read the generated FAQ file
            with open(out_file, 'r', encoding='utf-8') as f:
                faq_content = f.read()
            
            # Clean up temporary file
            if os.path.exists(out_file):
                os.remove(out_file)
            
            db.store_result(job_id, {
                'status': 'completed',
                'progress': 100,
                'message': 'FAQ generation completed successfully.',
                'created_at': datetime.now().isoformat(),
                'data': {
                    'faq_content': faq_content,
                    'url': url,
                    'language': language,
                    'platform': platform,
                    'faq_count': faq_count
                },
                'error': None
            })
        else:
            db.store_result(job_id, {
                'status': 'failed',
                'progress': 100,
                'message': 'FAQ generation failed. Please check the URL and try again.',
                'created_at': datetime.now().isoformat(),
                'data': None,
                'error': 'FAQ generation failed'
            })
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in process_faq_generation: {error_details}")

        db.store_result(job_id, {
            'status': 'failed',
            'progress': 100,
            'message': f"Error during processing: {str(e)}",
            'created_at': datetime.now().isoformat(),
            'data': None,
            'error': str(e)
        })
        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
