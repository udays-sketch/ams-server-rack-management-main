# Server Rack Change Detection Web Application - User Guide

## Overview

The Server Rack Change Detection Web Application is a powerful tool designed to help data center managers detect hardware changes in server racks using visual AI, and reconcile these findings with asset management records. This guide provides comprehensive instructions for using the application.

## Features

- **Visual AI Change Detection**: Upload before and after images of server racks to automatically detect hardware changes
- **Asset Management System**: Track and manage server rack assets with a comprehensive database
- **Reconciliation Engine**: Compare detected changes with asset records to identify discrepancies
- **Reporting System**: Generate detailed reports of discrepancies for review and action

## Getting Started

### Accessing the Application

The application is accessible at the following URL:
- [Server Rack Change Detection Web App](https://your-deployment-url.com)

### Navigation

The application consists of four main sections:

1. **Home**: Overview of the application and its capabilities
2. **Compare**: Upload and compare server rack images
3. **Asset Management**: View and manage server racks and assets
4. **Reports**: View and resolve discrepancies

## Using the Application

### Image Comparison

1. Navigate to the **Compare** page
2. Upload a "before" image of a server rack
3. Upload an "after" image of the same server rack
4. Select the rack ID from the dropdown menu
5. Click "Compare Images"
6. The system will process the images and display:
   - Side-by-side comparison with changes highlighted
   - List of detected changes with type, location, and confidence score
7. Click "Reconcile with AMS" to compare findings with asset records

### Asset Management

1. Navigate to the **Asset Management** page
2. View the list of server racks with utilization statistics
3. Click "View" to see details of a specific rack, including:
   - Visual rack layout showing asset positions
   - List of assets in the rack
4. Add new racks using the "Add Rack" button
5. Add new assets using the "Add Asset" button when viewing a rack
6. Edit or remove assets as needed

### Viewing and Resolving Discrepancies

1. Navigate to the **Reports** page
2. View open discrepancies sorted by severity
3. Click "View" to see details of a specific discrepancy, including:
   - Discrepancy type and description
   - Location information
   - AMS data vs. detected change data
   - Recommended action
4. Click "Resolve" to mark a discrepancy as resolved:
   - Enter your name in the "Resolved By" field
   - Add notes explaining how the discrepancy was resolved
   - Click "Confirm Resolution"
5. View resolved discrepancies in the "Resolved Discrepancies" section

## Workflow Examples

### Example 1: Detecting an Unregistered Server Addition

1. Take a "before" image of a server rack
2. Install a new server in the rack
3. Take an "after" image of the server rack
4. Upload both images in the Compare page
5. The system detects the addition and highlights it in red
6. Click "Reconcile with AMS"
7. The system identifies a discrepancy: "Unregistered Addition"
8. View the discrepancy details
9. Add the new server to the Asset Management System
10. Resolve the discrepancy with notes about the action taken

### Example 2: Verifying Rack Inventory

1. Take a current image of a server rack
2. Use the same image for both "before" and "after" (no changes)
3. The system should detect no changes (high SSIM score)
4. Reconcile with AMS to verify that physical reality matches records

## API Documentation

The application provides a RESTful API for integration with other systems:

### Image Comparison API

- **POST /api/compare**
  - Description: Compare before and after images
  - Parameters: before_image (file), after_image (file)
  - Returns: JSON with comparison results, including session_id, changes, and image paths

### Reconciliation API

- **POST /api/reconcile/{session_id}**
  - Description: Reconcile detected changes with AMS
  - Parameters: session_id (path), rack_id (body, optional)
  - Returns: JSON with discrepancies and report_id

### Asset Management API

- **GET /api/racks**
  - Description: Get all racks
  - Returns: JSON with rack list

- **GET /api/rack/{rack_id}/assets**
  - Description: Get assets in a specific rack
  - Parameters: rack_id (path)
  - Returns: JSON with asset list

- **GET /api/rack/{rack_id}/utilization**
  - Description: Get rack utilization statistics
  - Parameters: rack_id (path)
  - Returns: JSON with utilization data

### Discrepancy Management API

- **GET /api/discrepancy/{discrepancy_id}**
  - Description: Get discrepancy details
  - Parameters: discrepancy_id (path)
  - Returns: JSON with discrepancy details

- **POST /api/resolve-discrepancy/{discrepancy_id}**
  - Description: Resolve a discrepancy
  - Parameters: discrepancy_id (path), resolved_by (body), resolution_notes (body)
  - Returns: JSON with success status

## Troubleshooting

### Image Comparison Issues

- **Problem**: Images not comparing correctly
  - **Solution**: Ensure both images are of the same rack from the same angle
  - **Solution**: Check that images are clear and well-lit

- **Problem**: Changes not detected
  - **Solution**: Ensure the changes are visible in the images
  - **Solution**: Try adjusting the camera angle or lighting

### Asset Management Issues

- **Problem**: Cannot add an asset to a specific RU position
  - **Solution**: Check if the position is already occupied by another asset
  - **Solution**: Verify that the asset size fits within the available space

### Reconciliation Issues

- **Problem**: Discrepancies not appearing
  - **Solution**: Verify that the correct rack ID is selected
  - **Solution**: Check that the AMS has data for the selected rack

## Best Practices

1. **Image Capture**:
   - Use consistent lighting conditions
   - Maintain the same camera angle and distance
   - Ensure the entire rack is visible
   - Avoid reflections and shadows

2. **Asset Management**:
   - Keep asset information up to date
   - Use consistent naming conventions
   - Document all changes to the physical infrastructure

3. **Reconciliation**:
   - Regularly compare physical reality with AMS records
   - Promptly resolve discrepancies
   - Document the resolution process

## Technical Information

### System Requirements

- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)
- **Screen Resolution**: Minimum 1280x720
- **Internet Connection**: Required for accessing the web application

### Data Storage

- **Images**: Uploaded images are stored securely on the server
- **Asset Data**: Stored in a database with regular backups
- **Reports**: Generated reports are stored for historical reference

## Support and Feedback

For support or to provide feedback, please contact:
- Email: support@saltmine.com
- Phone: (555) 123-4567

## Privacy and Security

- All uploaded images and data are stored securely
- User actions are logged for audit purposes
- The application uses HTTPS for secure communication
