#!/usr/bin/env python3
"""
Reconciliation Module for Server Rack Change Detection Web App

This module provides functionality for reconciling detected changes from image analysis
with the asset management system (AMS) data.
Adapted from the original POC for web application use.
"""

import os
import json
import uuid
from datetime import datetime

class ChangeReconciliation:
    """
    A class for reconciling detected changes with AMS data.
    """
    
    def __init__(self, ams, results_folder):
        """
        Initialize the ChangeReconciliation with an AMS instance.
        
        Args:
            ams: Instance of the MockAMS
            results_folder (str): Path to store reconciliation results
        """
        self.ams = ams
        self.results_folder = results_folder
        self.discrepancies = []
        
        # Create folder if it doesn't exist
        os.makedirs(results_folder, exist_ok=True)
    
    def reconcile_changes(self, session_id, rack_id="RACK-001"):
        """
        Reconcile detected changes with AMS data.
        
        Args:
            session_id (str): Session ID from image comparison
            rack_id (str): Rack identifier in the AMS
            
        Returns:
            dict: Reconciliation results including discrepancies and report ID
        """
        # Load detected changes from the session
        changes_path = os.path.join(self.results_folder, session_id, "changes.json")
        
        if not os.path.exists(changes_path):
            raise ValueError(f"Changes file not found for session {session_id}")
        
        with open(changes_path, 'r') as f:
            detected_changes = json.load(f)
        
        # Get all assets in the rack from AMS
        ams_assets = self.ams.get_rack_assets(rack_id)
        
        # Clear previous discrepancies
        self.discrepancies = []
        
        # Process each detected change
        for change in detected_changes:
            change_id = change['id']
            change_type = change['type']
            ru_position = change['location']['estimated_ru']
            confidence = change['confidence']
            
            # Find asset in AMS at the detected RU position
            ams_asset = self.ams.get_asset_by_ru(rack_id, ru_position)
            
            # Apply business rules for reconciliation
            if change_type == "Addition":
                self._reconcile_addition(session_id, change, ams_asset, rack_id)
            elif change_type == "Removal":
                self._reconcile_removal(session_id, change, ams_asset, rack_id)
            elif change_type == "Modification" or change_type == "Relocation":
                self._reconcile_modification(session_id, change, ams_asset, rack_id)
        
        # Generate report
        report_id = self.generate_report(session_id)
        
        return {
            'session_id': session_id,
            'rack_id': rack_id,
            'discrepancies': self.discrepancies,
            'report_id': report_id
        }
    
    def _reconcile_addition(self, session_id, change, ams_asset, rack_id):
        """
        Reconcile an addition change.
        
        Args:
            session_id (str): Session ID from image comparison
            change (dict): Detected change
            ams_asset (dict): Asset from AMS at the change location
            rack_id (str): Rack identifier
        """
        change_id = change['id']
        ru_position = change['location']['estimated_ru']
        confidence = change['confidence']
        
        # If AMS shows no asset at this location, it's an unregistered addition
        if ams_asset is None:
            discrepancy_id = self.ams.add_discrepancy(
                session_id=session_id,
                change_id=change_id,
                discrepancy_type='Unregistered Addition',
                description=f"Hardware added at RU {ru_position} but not registered in AMS",
                rack_id=rack_id,
                ru_position=ru_position,
                confidence=confidence,
                severity='High',
                recommended_action='Register new hardware in AMS',
                ams_data=None,
                detected_data=change
            )
            
            if discrepancy_id:
                discrepancy = self.ams.get_discrepancy(discrepancy_id)
                if discrepancy:
                    self.discrepancies.append(discrepancy)
        else:
            # If AMS shows an asset with status other than 'Active', it's a status discrepancy
            if ams_asset['status'] != 'Active':
                discrepancy_id = self.ams.add_discrepancy(
                    session_id=session_id,
                    change_id=change_id,
                    discrepancy_type='Status Discrepancy',
                    description=f"Hardware at RU {ru_position} is physically present but has status '{ams_asset['status']}' in AMS",
                    rack_id=rack_id,
                    ru_position=ru_position,
                    confidence=confidence,
                    severity='Medium',
                    recommended_action='Update asset status in AMS to Active',
                    ams_data=ams_asset,
                    detected_data=change
                )
                
                if discrepancy_id:
                    discrepancy = self.ams.get_discrepancy(discrepancy_id)
                    if discrepancy:
                        self.discrepancies.append(discrepancy)
    
    def _reconcile_removal(self, session_id, change, ams_asset, rack_id):
        """
        Reconcile a removal change.
        
        Args:
            session_id (str): Session ID from image comparison
            change (dict): Detected change
            ams_asset (dict): Asset from AMS at the change location
            rack_id (str): Rack identifier
        """
        change_id = change['id']
        ru_position = change['location']['estimated_ru']
        confidence = change['confidence']
        
        # If AMS shows an asset at this location, it's an unregistered removal
        if ams_asset is not None:
            discrepancy_id = self.ams.add_discrepancy(
                session_id=session_id,
                change_id=change_id,
                discrepancy_type='Unregistered Removal',
                description=f"Hardware removed from RU {ru_position} but still registered as present in AMS",
                rack_id=rack_id,
                ru_position=ru_position,
                confidence=confidence,
                severity='High',
                recommended_action='Update AMS to reflect hardware removal',
                ams_data=ams_asset,
                detected_data=change
            )
            
            if discrepancy_id:
                discrepancy = self.ams.get_discrepancy(discrepancy_id)
                if discrepancy:
                    self.discrepancies.append(discrepancy)
    
    def _reconcile_modification(self, session_id, change, ams_asset, rack_id):
        """
        Reconcile a modification or relocation change.
        
        Args:
            session_id (str): Session ID from image comparison
            change (dict): Detected change
            ams_asset (dict): Asset from AMS at the change location
            rack_id (str): Rack identifier
        """
        change_id = change['id']
        ru_position = change['location']['estimated_ru']
        confidence = change['confidence']
        
        # If AMS shows no asset at this location, it's an unregistered modification
        if ams_asset is None:
            discrepancy_id = self.ams.add_discrepancy(
                session_id=session_id,
                change_id=change_id,
                discrepancy_type='Unregistered Modification',
                description=f"Hardware modified at RU {ru_position} but no asset registered at this location in AMS",
                rack_id=rack_id,
                ru_position=ru_position,
                confidence=confidence,
                severity='Medium',
                recommended_action='Investigate and update AMS accordingly',
                ams_data=None,
                detected_data=change
            )
            
            if discrepancy_id:
                discrepancy = self.ams.get_discrepancy(discrepancy_id)
                if discrepancy:
                    self.discrepancies.append(discrepancy)
        else:
            # If AMS shows an asset with different attributes, it's a configuration discrepancy
            # This is a simplified check - in a real system, you would compare more attributes
            discrepancy_id = self.ams.add_discrepancy(
                session_id=session_id,
                change_id=change_id,
                discrepancy_type='Configuration Discrepancy',
                description=f"Hardware at RU {ru_position} has been modified from its registered configuration",
                rack_id=rack_id,
                ru_position=ru_position,
                confidence=confidence,
                severity='Low',
                recommended_action='Verify hardware configuration and update AMS if needed',
                ams_data=ams_asset,
                detected_data=change
            )
            
            if discrepancy_id:
                discrepancy = self.ams.get_discrepancy(discrepancy_id)
                if discrepancy:
                    self.discrepancies.append(discrepancy)
    
    def generate_report(self, session_id):
        """
        Generate a reconciliation report.
        
        Args:
            session_id (str): Session ID from image comparison
            
        Returns:
            str: Report ID
        """
        # Generate a unique report ID
        report_id = uuid.uuid4().hex
        
        # Create report directory
        report_dir = os.path.join(self.results_folder, session_id, "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # Prepare report data
        report = {
            'report_id': report_id,
            'session_id': session_id,
            'total_discrepancies': len(self.discrepancies),
            'discrepancies_by_severity': {
                'High': len([d for d in self.discrepancies if d['severity'] == 'High']),
                'Medium': len([d for d in self.discrepancies if d['severity'] == 'Medium']),
                'Low': len([d for d in self.discrepancies if d['severity'] == 'Low'])
            },
            'discrepancies_by_type': {},
            'discrepancies': self.discrepancies,
            'generated_at': datetime.now().isoformat()
        }
        
        # Count discrepancies by type
        for d in self.discrepancies:
            d_type = d['type']
            if d_type not in report['discrepancies_by_type']:
                report['discrepancies_by_type'][d_type] = 0
            report['discrepancies_by_type'][d_type] += 1
        
        # Save to file
        json_path = os.path.join(report_dir, f"{report_id}.json")
        with open(json_path, 'w') as f:
            # Convert datetime objects to strings
            json.dump(report, f, indent=2, default=str)
        
        # Generate HTML report
        self.generate_html_report(report, report_dir, report_id)
        
        return report_id
    
    def generate_html_report(self, report, report_dir, report_id):
        """
        Generate an HTML reconciliation report.
        
        Args:
            report (dict): Report data
            report_dir (str): Directory to save the report
            report_id (str): Report ID
            
        Returns:
            str: Path to the HTML report
        """
        # Count discrepancies by severity and type
        high_severity = report['discrepancies_by_severity']['High']
        medium_severity = report['discrepancies_by_severity']['Medium']
        low_severity = report['discrepancies_by_severity']['Low']
        
        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Server Rack Change Reconciliation Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .summary {{
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }}
                .severity-high {{
                    color: #dc3545;
                }}
                .severity-medium {{
                    color: #fd7e14;
                }}
                .severity-low {{
                    color: #28a745;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .discrepancy-details {{
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 10px;
                }}
                .action-button {{
                    display: inline-block;
                    background-color: #007bff;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 4px;
                    text-decoration: none;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Server Rack Change Reconciliation Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Report ID: {report_id}</p>
                <p>Session ID: {report['session_id']}</p>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <p>Total Discrepancies: <strong>{len(report['discrepancies'])}</strong></p>
                    <p>Severity Breakdown:</p>
                    <ul>
                        <li class="severity-high">High: {high_severity}</li>
                        <li class="severity-medium">Medium: {medium_severity}</li>
                        <li class="severity-low">Low: {low_severity}</li>
                    </ul>
                    
                    <p>Discrepancy Types:</p>
                    <ul>
        """
        
        # Add discrepancy types
        for d_type, count in report['discrepancies_by_type'].items():
            html_content += f"<li>{d_type}: {count}</li>\n"
        
        html_content += """
                    </ul>
                </div>
                
                <h2>Discrepancies</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Type</th>
                        <th>Location</th>
                        <th>Severity</th>
                        <th>Recommended Action</th>
                    </tr>
        """
        
        # Add discrepancy rows
        for d in report['discrepancies']:
            severity_class = f"severity-{d['severity'].lower()}"
            html_content += f"""
            <tr>
                <td>{d['discrepancy_id']}</td>
                <td>{d['type']}</td>
                <td>Rack {d['rack_id']}, RU {d['ru_position']}</td>
                <td class="{severity_class}">{d['severity']}</td>
                <td>{d['recommended_action']}</td>
            </tr>
            """
        
        html_content += """
                </table>
                
                <h2>Detailed Discrepancy Information</h2>
        """
        
        # Add detailed discrepancy information
        for d in report['discrepancies']:
            severity_class = f"severity-{d['severity'].lower()}"
            
            # Convert ams_data and detected_data to formatted JSON strings
            ams_data_str = json.dumps(d['ams_data'], indent=2) if d['ams_data'] else 'No AMS data available'
            detected_data_str = json.dumps(d['detected_data'], indent=2)
            
            html_content += f"""
            <div class="discrepancy-details">
                <h3>Discrepancy #{d['discrepancy_id']}: {d['type']}</h3>
                <p><strong>Description:</strong> {d['description']}</p>
                <p><strong>Location:</strong> Rack {d['rack_id']}, RU {d['ru_position']}</p>
                <p><strong>Severity:</strong> <span class="{severity_class}">{d['severity']}</span></p>
                <p><strong>Confidence:</strong> {d['confidence']:.2f}</p>
                <p><strong>Recommended Action:</strong> {d['recommended_action']}</p>
                
                <h4>AMS Data:</h4>
                <pre>{ams_data_str}</pre>
                
                <h4>Detected Change:</h4>
                <pre>{detected_data_str}</pre>
                
                <a href="/resolve-discrepancy/{d['discrepancy_id']}" class="action-button">Resolve Discrepancy</a>
            </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        # Save to file
        html_path = os.path.join(report_dir, f"{report_id}.html")
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        return html_path
    
    def get_report(self, report_id, session_id):
        """
        Get a report by its ID.
        
        Args:
            report_id (str): Report ID
            session_id (str): Session ID
            
        Returns:
            dict: Report data or None if not found
        """
        report_path = os.path.join(self.results_folder, session_id, "reports", f"{report_id}.json")
        
        if not os.path.exists(report_path):
            return None
        
        with open(report_path, 'r') as f:
            return json.load(f)
    
    def get_report_html_path(self, report_id, session_id):
        """
        Get the path to the HTML report.
        
        Args:
            report_id (str): Report ID
            session_id (str): Session ID
            
        Returns:
            str: Path to the HTML report or None if not found
        """
        html_path = os.path.join(self.results_folder, session_id, "reports", f"{report_id}.html")
        
        if not os.path.exists(html_path):
            return None
        
        return html_path
