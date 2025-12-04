"""
Dapao User Templates Manager
Manages user-created custom prompt templates
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class DapaoUserTemplatesManager:
    """Manage user-created custom templates"""
    
    def __init__(self):
        """Initialize user templates manager"""
        self.base_dir = Path(__file__).parent
        self.user_templates_file = self.base_dir / "dapao_user_templates.json"
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load user templates from file"""
        if not self.user_templates_file.exists():
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "templates": []
            }
        
        try:
            with open(self.user_templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Dapao User Templates] Error loading templates: {e}")
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "templates": []
            }
    
    def _save_templates(self) -> bool:
        """Save user templates to file"""
        try:
            self.templates["updated_at"] = datetime.now().isoformat()
            with open(self.user_templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[Dapao User Templates] Error saving templates: {e}")
            return False
    
    def get_all_templates(self) -> List[Dict]:
        """Get all user templates"""
        return self.templates.get("templates", [])
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """Get a specific template by ID"""
        for template in self.templates.get("templates", []):
            if template.get("id") == template_id:
                return template
        return None
    
    def create_template(self, data: Dict) -> Dict:
        """
        Create a new template
        
        Required fields:
        - title: str
        - prompt_zh: str
        - prompt_en: str
        
        Optional fields:
        - description_zh: str
        - description_en: str
        - category: str
        - tags: List[str]
        - coverImage: str
        """
        # Generate ID
        template_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.templates['templates'])}"
        
        # Create template
        template = {
            "id": template_id,
            "title": data.get("title", "Untitled"),
            "prompt": {
                "zh": data.get("prompt_zh", ""),
                "en": data.get("prompt_en", "")
            },
            "description": {
                "zh": data.get("description_zh", ""),
                "en": data.get("description_en", "")
            },
            "category": data.get("category", "user_custom"),
            "tags": data.get("tags", ["custom"]),
            "coverImage": data.get("coverImage", ""),
            "images": [data.get("coverImage", "")] if data.get("coverImage") else [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source": "user_created"
        }
        
        # Add to templates list
        self.templates["templates"].append(template)
        
        # Save
        if self._save_templates():
            print(f"[Dapao User Templates] Created template: {template_id}")
            return {"success": True, "template": template}
        else:
            return {"success": False, "error": "Failed to save template"}
    
    def update_template(self, template_id: str, data: Dict) -> Dict:
        """Update an existing template"""
        for i, template in enumerate(self.templates["templates"]):
            if template.get("id") == template_id:
                # Update fields
                if "title" in data:
                    template["title"] = data["title"]
                if "prompt_zh" in data:
                    template["prompt"]["zh"] = data["prompt_zh"]
                if "prompt_en" in data:
                    template["prompt"]["en"] = data["prompt_en"]
                if "description_zh" in data:
                    template["description"]["zh"] = data["description_zh"]
                if "description_en" in data:
                    template["description"]["en"] = data["description_en"]
                if "category" in data:
                    template["category"] = data["category"]
                if "tags" in data:
                    template["tags"] = data["tags"]
                if "coverImage" in data:
                    template["coverImage"] = data["coverImage"]
                    # Update images list if coverImage changes and it's the only image or empty
                    if not template.get("images"):
                         template["images"] = [data["coverImage"]]
                    elif len(template["images"]) == 1 and template["images"][0] != data["coverImage"]:
                         template["images"] = [data["coverImage"]]
                
                template["updated_at"] = datetime.now().isoformat()
                
                # Save
                if self._save_templates():
                    print(f"[Dapao User Templates] Updated template: {template_id}")
                    return {"success": True, "template": template}
                else:
                    return {"success": False, "error": "Failed to save template"}
        
        return {"success": False, "error": "Template not found"}
    
    def delete_template(self, template_id: str) -> Dict:
        """Delete a template"""
        for i, template in enumerate(self.templates["templates"]):
            if template.get("id") == template_id:
                deleted = self.templates["templates"].pop(i)
                
                # Save
                if self._save_templates():
                    print(f"[Dapao User Templates] Deleted template: {template_id}")
                    return {"success": True, "deleted": deleted}
                else:
                    # Restore if save failed
                    self.templates["templates"].insert(i, deleted)
                    return {"success": False, "error": "Failed to save changes"}
        
        return {"success": False, "error": "Template not found"}
    
    def search_templates(self, keyword: str) -> List[Dict]:
        """Search user templates"""
        keyword_lower = keyword.lower()
        results = []
        
        for template in self.templates.get("templates", []):
            # Search in title
            if keyword_lower in template.get("title", "").lower():
                results.append(template)
                continue
            
            # Search in prompts
            if keyword_lower in template.get("prompt", {}).get("zh", "").lower():
                results.append(template)
                continue
            if keyword_lower in template.get("prompt", {}).get("en", "").lower():
                results.append(template)
                continue
            
            # Search in tags
            tags = template.get("tags", [])
            if any(keyword_lower in tag.lower() for tag in tags):
                results.append(template)
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about user templates"""
        templates = self.templates.get("templates", [])
        
        categories = {}
        for template in templates:
            cat = template.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total": len(templates),
            "categories": categories,
            "file_path": str(self.user_templates_file),
            "file_exists": self.user_templates_file.exists()
        }
