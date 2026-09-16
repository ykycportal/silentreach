#!/usr/bin/env python3
"""
Export results to Google Sheets
"""

import logging
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger("silentreach.export")

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


class SheetsExporter:
    """Export SilentReach results to Google Sheets."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or str(
            Path.home() / ".silentreach" / "google_credentials.json"
        )
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API."""
        if not HAS_GOOGLE:
            logger.warning("google-api-python-client not installed")
            return False
        
        try:
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.service = build('sheets', 'v4', credentials=creds)
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def create_sheet(
        self,
        spreadsheet_name: str,
        headers: List[str],
    ) -> Optional[str]:
        """Create a new Google Sheet with headers."""
        if not self.service:
            return None
        
        try:
            # Create spreadsheet
            spreadsheet = self.service.spreadsheets().create(
                body={
                    'properties': {
                        'title': spreadsheet_name,
                    }
                }
            ).execute()
            
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            
            # Add headers
            self.update_cell(spreadsheet_id, 'A1', headers)
            
            logger.info(f"Created sheet: {spreadsheet_name} (ID: {spreadsheet_id})")
            return spreadsheet_id
            
        except Exception as e:
            logger.error(f"Failed to create sheet: {e}")
            return None
    
    def append_data(
        self,
        spreadsheet_id: str,
        data: List[Dict],
        sheet_name: str = "Sheet1",
    ) -> bool:
        """Append data to existing sheet."""
        if not self.service:
            return False
        
        try:
            # Convert data to rows
            rows = []
            for item in data:
                row = list(item.values())
                rows.append(row)
            
            if not rows:
                return True
            
            # Find next empty row
            sheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                ranges=[sheet_name]
            ).execute()
            
            # Find last row with data
            last_row = 2  # Start after header
            for row in sheet.get('sheets', [{}])[0].get('data', []):
                if row.get('rowMetadata', {}).get('size', 0) > 0:
                    last_row = row.get('startRowIndex', 1) + 1
            
            # Append data
            range_name = f"{sheet_name}!A{last_row}"
            self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body={'values': rows}
            ).execute()
            
            logger.info(f"Appended {len(rows)} rows to {sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to append data: {e}")
            return False
    
    def update_cell(
        self,
        spreadsheet_id: str,
        cell: str,
        value,
    ) -> bool:
        """Update a single cell."""
        if not self.service:
            return False
        
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=cell,
                valueInputOption='USER_ENTERED',
                body={'values': [[value]]}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to update cell: {e}")
            return False
    
    def export_results(
        self,
        results: Dict,
        spreadsheet_id: Optional[str] = None,
        spreadsheet_name: Optional[str] = None,
    ) -> str:
        """Export scrape results to Google Sheets."""
        if not self.service:
            logger.error("Not authenticated with Google Sheets")
            return ""
        
        # Generate spreadsheet name if not provided
        if not spreadsheet_name:
            timestamp = results.get('timestamp', 'unknown')
            spreadsheet_name = f"SilentReach_{timestamp}"
        
        # Create or get spreadsheet
        if not spreadsheet_id:
            headers = ["Platform", "Query", "Title", "Author", "Score", "URL", "Timestamp"]
            spreadsheet_id = self.create_sheet(spreadsheet_name, headers)
            if not spreadsheet_id:
                return ""
        
        # Prepare data
        rows = []
        for platform, data in results.get("results", {}).items():
            for item in data.get("posts", data.get("videos", data.get("tweets", []))):
                row = [
                    platform,
                    data.get("query", ""),
                    item.get("title", ""),
                    item.get("author", ""),
                    item.get("score", ""),
                    item.get("link", item.get("url", "")),
                    item.get("timestamp", ""),
                ]
                rows.append(row)
        
        # Append to sheet
        if rows:
            self.append_data(spreadsheet_id, rows)
        
        logger.info(f"Exported {len(rows)} rows to Google Sheets")
        return spreadsheet_id
    
    def get_sheet_info(self, spreadsheet_id: str) -> Dict:
        """Get information about a spreadsheet."""
        if not self.service:
            return {}
        
        try:
            sheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            return {
                "id": spreadsheet_id,
                "title": sheet.get("properties", {}).get("title", ""),
                "sheets": [
                    s.get("properties", {}).get("title", "")
                    for s in sheet.get("sheets", [])
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get sheet info: {e}")
            return {}


if __name__ == "__main__":
    print("=== Google Sheets Export Test ===\n")
    print("To use this feature:")
    print("1. Create a Google Cloud project")
    print("2. Enable Google Sheets API")
    print("3. Create service account and download credentials")
    print("4. Save credentials to ~/.silentreach/google_credentials.json")
    print("5. Share your Google Sheet with the service account email")
    print("\nFor more info: https://developers.google.com/sheets/api/quickstart/python")
