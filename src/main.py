#!/usr/bin/env python3
"""
Main Flask application for Server Rack Change Detection Web App
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename

# Import models
from src.models.image_comparison import ServerRackChangeDetector
from src.models.mock_ams import MockAMS
from src.models.reconciliation import ChangeReconciliation

app = Flask(__name__)

# Configure app
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
app.config['RESULTS_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
app.config['MOCK_AMS_DB'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mock_ams', 'mock_ams.db')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(app.config['MOCK_AMS_DB']), exist_ok=True)

# Initialize models
ams = MockAMS(app.config['MOCK_AMS_DB'])
change_detector = ServerRackChangeDetector(app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER'])
reconciliation = ChangeReconciliation(ams, app.config['RESULTS_FOLDER'])

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/compare')
def compare_page():
    """Render the comparison page"""
    return render_template('compare.html')

@app.route('/assets')
def assets_page():
    """Render the asset management page"""
    racks = ams.get_all_racks()
    return render_template('assets.html', racks=racks)

@app.route('/reports')
def reports_page():
    """Render the reports page"""
    # Get all discrepancies
    discrepancies = ams.get_all_discrepancies()
    return render_template('reports.html', discrepancies=discrepancies)

@app.route('/demo')
def demo_page():
    """Render the demo page"""
    return render_template('demo.html')

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """API endpoint for image comparison"""
    try:
        # Check if both files are present
        if 'before_image' not in request.files or 'after_image' not in request.files:
            return jsonify({'success': False, 'message': 'Both before and after images are required'}), 400
        
        before_file = request.files['before_image']
        after_file = request.files['after_image']
        
        # Check if files are valid
        if before_file.filename == '' or after_file.filename == '':
            return jsonify({'success': False, 'message': 'No selected files'}), 400
        
        if not allowed_file(before_file.filename) or not allowed_file(after_file.filename):
            return jsonify({'success': False, 'message': 'Invalid file format. Allowed formats: png, jpg, jpeg, webp'}), 400
        
        try:
            # Save uploaded files
            before_path = change_detector.save_uploaded_image(before_file, 'before')
            after_path = change_detector.save_uploaded_image(after_file, 'after')
            
            # Compare images
            change_detector.compare_images(before_path, after_path)
            
            # Save results
            results = change_detector.save_results()
            session_id = results['session_id']
            
            # Get web paths for results
            web_paths = change_detector.get_web_paths(session_id)
            
            # Extract changes
            changes = change_detector.extract_change_details()
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'comparison_image': web_paths['comparison'],
                'visual_diff': web_paths['visual_diff'],
                'changes': changes,
                'changes_count': len(changes),
                'ssim_score': change_detector.results['ssim_score']
            })
        except Exception as e:
            import traceback
            app.logger.error(f"Error during image comparison: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({'success': False, 'message': f"Error processing images: {str(e)}"}), 500
    except Exception as outer_e:
        import traceback
        app.logger.error(f"Unhandled error in API: {str(outer_e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'Server error occurred'}), 500

@app.route('/api/reconcile/<session_id>', methods=['POST'])
def api_reconcile(session_id):
    """API endpoint for reconciliation"""
    try:
        # Get rack ID from request or use default
        rack_id = request.json.get('rack_id', 'RACK-001') if request.is_json else 'RACK-001'
        
        # Reconcile changes
        results = reconciliation.reconcile_changes(session_id, rack_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'rack_id': rack_id,
            'discrepancies': results['discrepancies'],
            'discrepancies_count': len(results['discrepancies']),
            'report_id': results['report_id']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/discrepancy/<discrepancy_id>')
def api_get_discrepancy(discrepancy_id):
    """API endpoint to get discrepancy details"""
    try:
        discrepancy = ams.get_discrepancy(discrepancy_id)
        
        if not discrepancy:
            return jsonify({'success': False, 'message': 'Discrepancy not found'}), 404
        
        return jsonify({
            'success': True,
            'discrepancy': discrepancy
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/resolve-discrepancy/<discrepancy_id>', methods=['POST'])
def api_resolve_discrepancy(discrepancy_id):
    """API endpoint to resolve a discrepancy"""
    try:
        # Get resolution notes from request or use default
        data = request.json if request.is_json else {}
        resolved_by = data.get('resolved_by', 'Web User')
        resolution_notes = data.get('resolution_notes', 'Resolved via web interface')
        
        # Resolve discrepancy
        success = ams.resolve_discrepancy(discrepancy_id, resolved_by, resolution_notes)
        
        if not success:
            return jsonify({'success': False, 'message': 'Failed to resolve discrepancy'}), 500
        
        return jsonify({
            'success': True,
            'discrepancy_id': discrepancy_id,
            'message': 'Discrepancy resolved successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/racks')
def api_get_racks():
    """API endpoint to get all racks"""
    try:
        racks = ams.get_all_racks()
        return jsonify({
            'success': True,
            'racks': racks
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/rack/<rack_id>/assets')
def api_get_rack_assets(rack_id):
    """API endpoint to get assets in a rack"""
    try:
        assets = ams.get_rack_assets(rack_id)
        return jsonify({
            'success': True,
            'rack_id': rack_id,
            'assets': assets
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/rack/<rack_id>/utilization')
def api_get_rack_utilization(rack_id):
    """API endpoint to get rack utilization"""
    try:
        utilization = ams.get_rack_utilization(rack_id)
        
        if not utilization:
            return jsonify({'success': False, 'message': 'Rack not found'}), 404
        
        return jsonify({
            'success': True,
            'utilization': utilization
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/asset/<asset_id>')
def api_get_asset(asset_id):
    """API endpoint to get asset details"""
    try:
        asset = ams.get_asset_by_id(asset_id)
        
        if not asset:
            return jsonify({'success': False, 'message': 'Asset not found'}), 404
        
        return jsonify({
            'success': True,
            'asset': asset
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/report/<report_id>/<session_id>')
def api_get_report(report_id, session_id):
    """API endpoint to get report details"""
    try:
        report = reconciliation.get_report(report_id, session_id)
        
        if not report:
            return jsonify({'success': False, 'message': 'Report not found'}), 404
        
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/report/<report_id>/<session_id>')
def view_report(report_id, session_id):
    """View HTML report"""
    try:
        html_path = reconciliation.get_report_html_path(report_id, session_id)
        
        if not html_path:
            abort(404)
        
        # Read the HTML file
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        return html_content
    except Exception as e:
        abort(500)

@app.route('/results/<path:filename>')
def results_files(filename):
    """Serve result files"""
    return send_from_directory(app.config['RESULTS_FOLDER'], filename)

@app.route('/uploads/<path:filename>')
def uploaded_files(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
