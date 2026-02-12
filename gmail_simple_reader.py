#!/usr/bin/env python3
"""
Gmail Simple Reader — HTTP directo, sin librerías Google
Más ligero, más rápido, menos dependencias
"""

import json
import requests
import base64
from datetime import datetime

class SimpleGmailReader:
    """Read Gmail using raw HTTP API"""
    
    def __init__(self):
        self.token = self._load_token()
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
    
    def _load_token(self):
        with open('/home/lumen/.openclaw/workspace/secrets/gmail_token.json') as f:
            data = json.load(f)
            return data['token']
    
    def get_unread(self, max_results=10):
        """Get unread emails"""
        url = f"{self.base_url}/users/me/messages"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "q": "is:unread in:inbox",
            "maxResults": max_results
        }
        
        resp = requests.get(url, headers=headers, params=params)
        
        if resp.status_code != 200:
            return {"error": resp.text}
        
        data = resp.json()
        messages = data.get('messages', [])
        
        results = []
        for msg in messages[:5]:  # Get details for first 5
            msg_detail = self._get_message(msg['id'])
            if msg_detail:
                results.append(msg_detail)
        
        return results
    
    def _get_message(self, msg_id):
        """Get message details"""
        url = f"{self.base_url}/users/me/messages/{msg_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"format": "full"}
        
        resp = requests.get(url, headers=headers, params=params)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        payload = data.get('payload', {})
        header_list = payload.get('headers', [])
        
        # Find specific headers
        header_dict = {}
        for h in header_list:
            if isinstance(h, dict) and 'name' in h and 'value' in h:
                header_dict[h['name']] = h['value']
        
        return {
            "id": msg_id,
            "subject": header_dict.get('Subject', 'No Subject'),
            "from": header_dict.get('From', 'Unknown'),
            "date": header_dict.get('Date', 'Unknown'),
            "snippet": data.get('snippet', '')[:100]
        }
    
    def check_replies_from(self, addresses, hours=2):
        """Check for replies from specific addresses"""
        # Format: from:addr1 OR from:addr2
        query = " OR ".join([f"from:{a}" for a in addresses])
        
        url = f"{self.base_url}/users/me/messages"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"q": query, "maxResults": 20}
        
        resp = requests.get(url, headers=headers, params=params)
        
        if resp.status_code != 200:
            return {"error": resp.text}
        
        data = resp.json()
        messages = data.get('messages', [])
        
        results = []
        for msg in messages:
            detail = self._get_message(msg['id'])
            if detail:
                results.append(detail)
        
        return results

def main():
    reader = SimpleGmailReader()
    
    print("📧 Leyendo inbox...")
    unread = reader.get_unread(5)
    
    print("\n🆕 Unread emails:")
    for email in unread:
        if "error" in email:
            print(f"  Error: {email['error']}")
            continue
        print(f"\n  From: {email['from'][:40]}")
        print(f"  Subject: {email['subject'][:50]}")
        print(f"  Preview: {email['snippet']}...")
    
    print("\n" + "="*50)
    print("🔍 Checking replies from Kiri & Raul...")
    
    replies = reader.check_replies_from([
        "kiriabravo@hotmail.com",
        "raulbouche1@gmail.com"
    ])
    
    if replies:
        print(f"\n🎉 {len(replies)} mensajes encontrados!")
        for r in replies:
            print(f"  • {r['from']}: {r['subject'][:40]}")
    else:
        print("\n⏳ No replies yet (emails sent 20:55)")

if __name__ == "__main__":
    main()
