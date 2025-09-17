#!/usr/bin/env python3
"""
Mock Asset Management System (AMS) for Server Rack Change Detection Web App

This module provides a simple mock AMS for storing and retrieving server rack asset data.
Adapted from the original POC for web application use.
"""

import os
import json
import sqlite3
from datetime import datetime
import uuid

class MockAMS:
    """
    A simple mock Asset Management System for server rack assets.
    """
    
    def __init__(self, db_path):
        """
        Initialize the MockAMS with a database path.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """
        Initialize the database schema if it doesn't exist.
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create racks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS racks (
            rack_id TEXT PRIMARY KEY,
            location TEXT,
            description TEXT,
            total_ru INTEGER,
            last_updated TIMESTAMP
        )
        ''')
        
        # Create assets table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            asset_id TEXT PRIMARY KEY,
            rack_id TEXT,
            ru_position INTEGER,
            ru_size INTEGER,
            asset_type TEXT,
            model TEXT,
            serial_number TEXT,
            status TEXT,
            installation_date TIMESTAMP,
            last_updated TIMESTAMP,
            FOREIGN KEY (rack_id) REFERENCES racks(rack_id)
        )
        ''')
        
        # Create change_history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS change_history (
            change_id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT,
            rack_id TEXT,
            change_type TEXT,
            old_ru_position INTEGER,
            new_ru_position INTEGER,
            change_date TIMESTAMP,
            change_by TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
            FOREIGN KEY (rack_id) REFERENCES racks(rack_id)
        )
        ''')
        
        # Create discrepancies table for web app
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS discrepancies (
            discrepancy_id TEXT PRIMARY KEY,
            session_id TEXT,
            change_id INTEGER,
            type TEXT,
            description TEXT,
            rack_id TEXT,
            ru_position INTEGER,
            confidence REAL,
            severity TEXT,
            status TEXT,
            recommended_action TEXT,
            ams_data TEXT,
            detected_data TEXT,
            created_at TIMESTAMP,
            resolved_at TIMESTAMP,
            resolved_by TEXT,
            resolution_notes TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # Check if we need to populate sample data
        self._check_and_populate_sample_data()
    
    def _check_and_populate_sample_data(self):
        """
        Check if the database is empty and populate with sample data if needed.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if racks table is empty
        cursor.execute('SELECT COUNT(*) FROM racks')
        rack_count = cursor.fetchone()[0]
        
        conn.close()
        
        # If no racks exist, populate with sample data
        if rack_count == 0:
            self.populate_sample_data()
    
    def add_rack(self, rack_id, location, description, total_ru=42):
        """
        Add a new rack to the AMS.
        
        Args:
            rack_id (str): Unique identifier for the rack
            location (str): Physical location of the rack
            description (str): Description of the rack
            total_ru (int): Total rack units available (default: 42)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO racks (rack_id, location, description, total_ru, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ''', (rack_id, location, description, total_ru, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding rack: {e}")
            return False
    
    def add_asset(self, asset_id, rack_id, ru_position, ru_size, asset_type, model, serial_number, status="Active"):
        """
        Add a new asset to the AMS.
        
        Args:
            asset_id (str): Unique identifier for the asset
            rack_id (str): Rack identifier where the asset is installed
            ru_position (int): Rack unit position (bottom-up)
            ru_size (int): Number of rack units the asset occupies
            asset_type (str): Type of asset (e.g., Server, Switch, Storage)
            model (str): Model of the asset
            serial_number (str): Serial number of the asset
            status (str): Status of the asset (default: Active)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if the rack exists
            cursor.execute('SELECT rack_id FROM racks WHERE rack_id = ?', (rack_id,))
            if not cursor.fetchone():
                print(f"Rack {rack_id} does not exist")
                conn.close()
                return False
            
            # Check if the asset already exists
            cursor.execute('SELECT asset_id FROM assets WHERE asset_id = ?', (asset_id,))
            if cursor.fetchone():
                print(f"Asset {asset_id} already exists")
                conn.close()
                return False
            
            # Check if the rack unit is available
            cursor.execute('''
            SELECT asset_id FROM assets 
            WHERE rack_id = ? AND 
                  ((ru_position <= ? AND ru_position + ru_size - 1 >= ?) OR
                   (ru_position >= ? AND ru_position <= ? + ? - 1))
            ''', (rack_id, ru_position, ru_position, ru_position, ru_position, ru_size))
            
            if cursor.fetchone():
                print(f"Rack unit {ru_position} in rack {rack_id} is already occupied")
                conn.close()
                return False
            
            # Add the asset
            cursor.execute('''
            INSERT INTO assets (
                asset_id, rack_id, ru_position, ru_size, asset_type, model, 
                serial_number, status, installation_date, last_updated
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset_id, rack_id, ru_position, ru_size, asset_type, model,
                serial_number, status, datetime.now(), datetime.now()
            ))
            
            # Add to change history
            cursor.execute('''
            INSERT INTO change_history (
                asset_id, rack_id, change_type, new_ru_position, change_date, change_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                asset_id, rack_id, "Installation", ru_position, datetime.now(), "System"
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding asset: {e}")
            return False
    
    def update_asset(self, asset_id, **kwargs):
        """
        Update an existing asset in the AMS.
        
        Args:
            asset_id (str): Unique identifier for the asset
            **kwargs: Fields to update (e.g., rack_id, ru_position, status)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if the asset exists
            cursor.execute('SELECT * FROM assets WHERE asset_id = ?', (asset_id,))
            asset = cursor.fetchone()
            if not asset:
                print(f"Asset {asset_id} does not exist")
                conn.close()
                return False
            
            # Get column names
            cursor.execute('PRAGMA table_info(assets)')
            columns = [col[1] for col in cursor.fetchall()]
            
            # Build update query
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in columns:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if not updates:
                print("No valid fields to update")
                conn.close()
                return False
            
            # Add last_updated timestamp
            updates.append("last_updated = ?")
            values.append(datetime.now())
            
            # Add asset_id for WHERE clause
            values.append(asset_id)
            
            # Execute update
            cursor.execute(f'''
            UPDATE assets SET {", ".join(updates)} WHERE asset_id = ?
            ''', values)
            
            # Add to change history if ru_position changed
            if 'ru_position' in kwargs:
                old_ru = asset[2]  # Assuming ru_position is the 3rd column
                new_ru = kwargs['ru_position']
                
                cursor.execute('''
                INSERT INTO change_history (
                    asset_id, rack_id, change_type, old_ru_position, new_ru_position, change_date, change_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    asset_id, asset[1], "Relocation", old_ru, new_ru, datetime.now(), "System"
                ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating asset: {e}")
            return False
    
    def remove_asset(self, asset_id):
        """
        Remove an asset from the AMS.
        
        Args:
            asset_id (str): Unique identifier for the asset
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if the asset exists
            cursor.execute('SELECT rack_id, ru_position FROM assets WHERE asset_id = ?', (asset_id,))
            asset = cursor.fetchone()
            if not asset:
                print(f"Asset {asset_id} does not exist")
                conn.close()
                return False
            
            rack_id, ru_position = asset
            
            # Add to change history
            cursor.execute('''
            INSERT INTO change_history (
                asset_id, rack_id, change_type, old_ru_position, change_date, change_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                asset_id, rack_id, "Removal", ru_position, datetime.now(), "System"
            ))
            
            # Remove the asset
            cursor.execute('DELETE FROM assets WHERE asset_id = ?', (asset_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error removing asset: {e}")
            return False
    
    def get_all_racks(self):
        """
        Get all racks in the AMS.
        
        Returns:
            list: List of all racks
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM racks ORDER BY rack_id')
            
            racks = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return racks
        except Exception as e:
            print(f"Error getting all racks: {e}")
            return []
    
    def get_rack_assets(self, rack_id):
        """
        Get all assets in a specific rack.
        
        Args:
            rack_id (str): Rack identifier
            
        Returns:
            list: List of assets in the rack
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM assets WHERE rack_id = ? ORDER BY ru_position
            ''', (rack_id,))
            
            assets = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return assets
        except Exception as e:
            print(f"Error getting rack assets: {e}")
            return []
    
    def get_asset_by_ru(self, rack_id, ru_position):
        """
        Get asset at a specific rack unit position.
        
        Args:
            rack_id (str): Rack identifier
            ru_position (int): Rack unit position
            
        Returns:
            dict: Asset information or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM assets 
            WHERE rack_id = ? AND ru_position <= ? AND ru_position + ru_size - 1 >= ?
            ''', (rack_id, ru_position, ru_position))
            
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
        except Exception as e:
            print(f"Error getting asset by RU: {e}")
            return None
    
    def get_asset_by_id(self, asset_id):
        """
        Get asset by its unique identifier.
        
        Args:
            asset_id (str): Asset identifier
            
        Returns:
            dict: Asset information or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM assets WHERE asset_id = ?', (asset_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
        except Exception as e:
            print(f"Error getting asset by ID: {e}")
            return None
    
    def get_asset_by_serial(self, serial_number):
        """
        Get asset by its serial number.
        
        Args:
            serial_number (str): Serial number
            
        Returns:
            dict: Asset information or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM assets WHERE serial_number = ?', (serial_number,))
            
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
        except Exception as e:
            print(f"Error getting asset by serial: {e}")
            return None
    
    def get_rack_utilization(self, rack_id):
        """
        Get rack utilization statistics.
        
        Args:
            rack_id (str): Rack identifier
            
        Returns:
            dict: Utilization statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total RUs in the rack
            cursor.execute('SELECT total_ru FROM racks WHERE rack_id = ?', (rack_id,))
            total_ru = cursor.fetchone()
            if not total_ru:
                print(f"Rack {rack_id} does not exist")
                conn.close()
                return None
            
            total_ru = total_ru[0]
            
            # Get all assets in the rack
            cursor.execute('''
            SELECT ru_position, ru_size FROM assets WHERE rack_id = ?
            ''', (rack_id,))
            
            assets = cursor.fetchall()
            used_ru = sum(ru_size for _, ru_size in assets)
            
            conn.close()
            
            return {
                'rack_id': rack_id,
                'total_ru': total_ru,
                'used_ru': used_ru,
                'available_ru': total_ru - used_ru,
                'utilization_percentage': (used_ru / total_ru) * 100 if total_ru > 0 else 0,
                'asset_count': len(assets)
            }
        except Exception as e:
            print(f"Error getting rack utilization: {e}")
            return None
    
    def add_discrepancy(self, session_id, change_id, discrepancy_type, description, rack_id, 
                        ru_position, confidence, severity, recommended_action, ams_data, detected_data):
        """
        Add a new discrepancy to the AMS.
        
        Args:
            session_id (str): Session ID from image comparison
            change_id (int): Change ID from image comparison
            discrepancy_type (str): Type of discrepancy
            description (str): Description of the discrepancy
            rack_id (str): Rack identifier
            ru_position (int): Rack unit position
            confidence (float): Confidence score
            severity (str): Severity level (High, Medium, Low)
            recommended_action (str): Recommended action to resolve
            ams_data (dict): Asset data from AMS
            detected_data (dict): Detected change data
            
        Returns:
            str: Discrepancy ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            discrepancy_id = str(uuid.uuid4())
            
            # Convert dict to JSON string
            ams_data_json = json.dumps(ams_data) if ams_data else None
            detected_data_json = json.dumps(detected_data) if detected_data else None
            
            cursor.execute('''
            INSERT INTO discrepancies (
                discrepancy_id, session_id, change_id, type, description, rack_id,
                ru_position, confidence, severity, status, recommended_action,
                ams_data, detected_data, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                discrepancy_id, session_id, change_id, discrepancy_type, description, rack_id,
                ru_position, confidence, severity, "Open", recommended_action,
                ams_data_json, detected_data_json, datetime.now()
            ))
            
            conn.commit()
            conn.close()
            return discrepancy_id
        except Exception as e:
            print(f"Error adding discrepancy: {e}")
            return None
    
    def get_discrepancy(self, discrepancy_id):
        """
        Get a discrepancy by its ID.
        
        Args:
            discrepancy_id (str): Discrepancy identifier
            
        Returns:
            dict: Discrepancy information or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM discrepancies WHERE discrepancy_id = ?', (discrepancy_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            discrepancy = dict(row)
            
            # Parse JSON strings back to dicts
            if discrepancy['ams_data']:
                discrepancy['ams_data'] = json.loads(discrepancy['ams_data'])
            
            if discrepancy['detected_data']:
                discrepancy['detected_data'] = json.loads(discrepancy['detected_data'])
            
            conn.close()
            return discrepancy
        except Exception as e:
            print(f"Error getting discrepancy: {e}")
            return None
    
    def get_discrepancies_by_session(self, session_id):
        """
        Get all discrepancies for a specific session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            list: List of discrepancies
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM discrepancies WHERE session_id = ? ORDER BY created_at DESC', (session_id,))
            
            discrepancies = []
            for row in cursor.fetchall():
                discrepancy = dict(row)
                
                # Parse JSON strings back to dicts
                if discrepancy['ams_data']:
                    discrepancy['ams_data'] = json.loads(discrepancy['ams_data'])
                
                if discrepancy['detected_data']:
                    discrepancy['detected_data'] = json.loads(discrepancy['detected_data'])
                
                discrepancies.append(discrepancy)
            
            conn.close()
            return discrepancies
        except Exception as e:
            print(f"Error getting discrepancies by session: {e}")
            return []
    
    def get_all_discrepancies(self, status=None):
        """
        Get all discrepancies, optionally filtered by status.
        
        Args:
            status (str, optional): Filter by status (Open, Resolved)
            
        Returns:
            list: List of discrepancies
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if status:
                cursor.execute('SELECT * FROM discrepancies WHERE status = ? ORDER BY created_at DESC', (status,))
            else:
                cursor.execute('SELECT * FROM discrepancies ORDER BY created_at DESC')
            
            discrepancies = []
            for row in cursor.fetchall():
                discrepancy = dict(row)
                
                # Parse JSON strings back to dicts
                if discrepancy['ams_data']:
                    discrepancy['ams_data'] = json.loads(discrepancy['ams_data'])
                
                if discrepancy['detected_data']:
                    discrepancy['detected_data'] = json.loads(discrepancy['detected_data'])
                
                discrepancies.append(discrepancy)
            
            conn.close()
            return discrepancies
        except Exception as e:
            print(f"Error getting all discrepancies: {e}")
            return []
    
    def resolve_discrepancy(self, discrepancy_id, resolved_by, resolution_notes):
        """
        Mark a discrepancy as resolved.
        
        Args:
            discrepancy_id (str): Discrepancy identifier
            resolved_by (str): User who resolved the discrepancy
            resolution_notes (str): Notes on how the discrepancy was resolved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE discrepancies SET
                status = ?,
                resolved_at = ?,
                resolved_by = ?,
                resolution_notes = ?
            WHERE discrepancy_id = ?
            ''', ("Resolved", datetime.now(), resolved_by, resolution_notes, discrepancy_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error resolving discrepancy: {e}")
            return False
    
    def populate_sample_data(self):
        """
        Populate the AMS with sample data for demonstration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add a sample rack
            self.add_rack('RACK-001', 'Server Room A', 'Primary Web Server Rack', 42)
            
            # Add sample assets
            assets = [
                ('ASSET-001', 'RACK-001', 1, 2, 'UPS', 'APC Smart-UPS 1500', 'SN12345678', 'Active'),
                ('ASSET-002', 'RACK-001', 3, 1, 'PDU', 'APC AP7900', 'SN23456789', 'Active'),
                ('ASSET-003', 'RACK-001', 5, 1, 'Switch', 'Cisco Catalyst 3850-48T', 'SN34567890', 'Active'),
                ('ASSET-004', 'RACK-001', 7, 2, 'Server', 'Dell PowerEdge R740', 'SN45678901', 'Active'),
                ('ASSET-005', 'RACK-001', 10, 2, 'Server', 'Dell PowerEdge R740', 'SN56789012', 'Active'),
                ('ASSET-006', 'RACK-001', 13, 2, 'Server', 'HP ProLiant DL380 Gen10', 'SN67890123', 'Active'),
                ('ASSET-007', 'RACK-001', 16, 3, 'Storage', 'NetApp FAS2750', 'SN78901234', 'Active'),
                ('ASSET-008', 'RACK-001', 20, 2, 'Server', 'Dell PowerEdge R740', 'SN89012345', 'Active'),
                ('ASSET-009', 'RACK-001', 23, 2, 'Server', 'HP ProLiant DL380 Gen10', 'SN90123456', 'Active'),
                ('ASSET-010', 'RACK-001', 26, 2, 'Server', 'Dell PowerEdge R740', 'SN01234567', 'Active'),
                ('ASSET-011', 'RACK-001', 29, 1, 'Switch', 'Cisco Nexus 9300', 'SN12345670', 'Active'),
                ('ASSET-012', 'RACK-001', 31, 2, 'Server', 'HP ProLiant DL380 Gen10', 'SN23456701', 'Active'),
                ('ASSET-013', 'RACK-001', 34, 2, 'Server', 'Dell PowerEdge R740', 'SN34567012', 'Active'),
                ('ASSET-014', 'RACK-001', 37, 2, 'Server', 'HP ProLiant DL380 Gen10', 'SN45670123', 'Active'),
                ('ASSET-015', 'RACK-001', 40, 1, 'KVM', 'Dell KVM Console Switch', 'SN56701234', 'Active'),
            ]
            
            for asset in assets:
                self.add_asset(*asset)
            
            return True
        except Exception as e:
            print(f"Error populating sample data: {e}")
            return False
