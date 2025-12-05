import json
import re
from pathlib import Path
from typing import Dict, List, Any

class DapaoPromptTemplateAdapter:
    """
    Adapter for Dapao Image Prompts
    Manages "Text-to-Image" and "Image Editing" categories.
    """
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        
        # Paths
        self.internal_json = self.base_dir / "bananapro-image-prompts-master/gpt4o-image-prompts-master/data/prompts.json"
        # External paths provided by user
        # self.external_json = Path(r"C:\Users\upboy\Desktop\参考提示词\gpt4o-image-prompts\data\prompts.json")
        self.external_json = self.base_dir / "external_prompts.json" # 默认指向项目内的一个不存在的文件，避免报错
        
        # ZHO模板路径修正为相对路径
        self.zho_readme = self.base_dir / "bananapro-image-prompts-master/README.md"
        
        self.templates = []
        
        # Fixed Categories
        self.categories = {
            "text_to_image": {
                "id": "text_to_image",
                "name_zh": "文生图提示词模板",
                "name_en": "Text-to-Image Prompts",
                "count": 0
            },
            "image_editing": {
                "id": "image_editing",
                "name_zh": "图像编辑提示词模板",
                "name_en": "Image Editing Prompts",
                "count": 0
            }
        }
        
        self._load_all_data()

    def _load_all_data(self):
        """Load data from all sources and merge"""
        print("[Dapao] Loading templates...")
        
        # 1. Load Text-to-Image (Internal + External)
        t2i_templates = self._load_gpt4o_templates()
        
        # 2. Load Image Editing (ZHO)
        ie_templates = self._load_zho_templates()
        
        # Combine
        self.templates = t2i_templates + ie_templates
        
        # Update counts
        self.categories['text_to_image']['count'] = len(t2i_templates)
        self.categories['image_editing']['count'] = len(ie_templates)
        
        print(f"[Dapao] Loaded {len(self.templates)} total templates")
        print(f"  - Text-to-Image: {len(t2i_templates)}")
        print(f"  - Image Editing: {len(ie_templates)}")

    def _load_gpt4o_templates(self) -> List[Dict]:
        loaded_templates = []
        seen_prompts = set()
        
        def process_file(file_path):
            if not file_path.exists():
                print(f"[Dapao] Warning: File not found {file_path}")
                return
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                items = data.get('items', [])
                for item in items:
                    prompts_list = item.get('prompts', [])
                    if not prompts_list:
                        continue
                    
                    # Deduplication key: First prompt text (English usually)
                    dedup_key = prompts_list[0].strip()
                    if dedup_key in seen_prompts:
                        continue
                    
                    seen_prompts.add(dedup_key)
                    
                    # Fix image path
                    # JSON has "images/xxx.jpeg", we want "/dapao/images/xxx.jpeg"
                    cover_img = item.get('coverImage', '')
                    if cover_img.startswith('images/'):
                        filename = cover_img.split('/')[-1]
                        item['coverImage'] = f"/dapao/images/{filename}"
                    
                    # Also fix 'images' list
                    fixed_images = []
                    for img in item.get('images', []):
                        if img.startswith('images/'):
                            fname = img.split('/')[-1]
                            fixed_images.append(f"/dapao/images/{fname}")
                        else:
                            fixed_images.append(img)
                    item['images'] = fixed_images
                    
                    # Tag for internal filtering
                    item['_dapao_category'] = 'text_to_image'
                    
                    loaded_templates.append(item)
                    
            except Exception as e:
                print(f"[Dapao] Error reading {file_path}: {e}")

        # Load internal first
        process_file(self.internal_json)
        # Load external
        process_file(self.external_json)
        
        # Sort by ID descending (Newest first)
        loaded_templates.sort(key=lambda x: int(x.get('id', 0)), reverse=True)
        return loaded_templates

    def _load_zho_templates(self) -> List[Dict]:
        templates = []
        if not self.zho_readme.exists():
            print("[Dapao] ZHO README not found")
            return []
            
        try:
            content = self.zho_readme.read_text(encoding='utf-8')
            
            # Split by "## " headers
            # This regex splits but captures delimiters if in parens. 
            # We use simple split and manual reconstruction or just findall
            
            # Strategy: Iterate through lines, find "## ", start new section
            lines = content.split('\n')
            current_section = []
            current_title = ""
            
            # Skip header
            start_parsing = False
            
            sections = []
            buffer = []
            
            for line in lines:
                if line.strip().startswith('## '):
                    if buffer:
                        sections.append(buffer)
                    buffer = [line]
                else:
                    buffer.append(line)
            if buffer:
                sections.append(buffer)
                
            for i, section_lines in enumerate(sections):
                section_text = '\n'.join(section_lines)
                title_line = section_lines[0].strip().replace('## ', '').strip()
                
                # Filter: Must contain "Prompt：" or "Prompt:"
                if "Prompt" not in section_text:
                    continue
                    
                # Extract Prompt
                # Find content between ``` and ```
                code_blocks = re.findall(r'```(.*?)```', section_text, re.DOTALL)
                if not code_blocks:
                    continue
                    
                # Use the first code block as prompt
                prompt_text = code_blocks[0].strip()
                
                # Extract Image
                # Try to find github image url
                # src="..." or markdown ![...](...)
                cover_image = ""
                img_match = re.search(r'src="(https://[^"]+)"', section_text)
                if img_match:
                    cover_image = img_match.group(1)
                else:
                    md_img = re.search(r'!\[.*?\]\((https://.*?)\)', section_text)
                    if md_img:
                        cover_image = md_img.group(1)
                        
                # Clean Title (remove emojis if needed, but user might like them)
                # ZHO uses "1️⃣ Title", "2️⃣ Title". We keep them.
                
                template = {
                    "id": f"zho_{i}",
                    "title": title_line,
                    "description": "Nano-Banana Creation ZHO Playstyle",
                    "prompts": [prompt_text],
                    "tags": ["image_editing", "zho"],
                    "coverImage": cover_image,
                    "images": [cover_image] if cover_image else [],
                    "_dapao_category": "image_editing",
                    "source": {
                        "name": "ZHO",
                        "url": "https://github.com/ZHO-ZHO-ZHO/Nano-Banana-Creation"
                    }
                }
                templates.append(template)
                
        except Exception as e:
            print(f"[Dapao] Error parsing ZHO README: {e}")
            import traceback
            traceback.print_exc()
            
        return templates

    def get_all_categories(self, lang: str = 'zh') -> List[Dict[str, Any]]:
        cats = [self.categories['text_to_image'], self.categories['image_editing']]
        result = []
        for c in cats:
             name_key = 'name_zh' if lang == 'zh' else 'name_en'
             result.append({
                 'id': c['id'],
                 'name': c[name_key],
                 'count': c['count']
             })
        return result

    def get_templates_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        filtered = []
        for t in self.templates:
            if t.get('_dapao_category') == category_id:
                prompts = t.get('prompts', [])
                prompt_en = prompts[0] if prompts else ""
                
                # ZHO templates only have one prompt usually (English)
                # GPT4o templates have [En, Zh] or [Zh]
                
                prompt_zh = ""
                if len(prompts) > 1:
                    prompt_zh = prompts[1]
                else:
                    # If only one prompt, reuse it for both if needed, or just leave ZH empty?
                    # Dapao UI expects bilingual?
                    # If source is ZHO, prompt is usually English code.
                    # If source is GPT4o, prompts[0] is English.
                    prompt_zh = prompt_en # Fallback to show something
                
                filtered.append({
                    'id': t.get('id'),
                    'title': t.get('title', ''),
                    'description': {
                        'zh': t.get('description', ''),
                        'en': t.get('description', '')
                    },
                    'tags': t.get('tags', []),
                    'coverImage': t.get('coverImage', ''),
                    'images': t.get('images', []),
                    'prompt': {
                        'zh': prompt_zh,
                        'en': prompt_en
                    },
                    'source': t.get('source', {})
                })
        return filtered
    
    def get_template_by_id(self, template_id) -> Dict[str, Any]:
        # Handle string/int mismatch
        tid_str = str(template_id)
        for t in self.templates:
            if str(t.get('id')) == tid_str:
                return t
        return {}
