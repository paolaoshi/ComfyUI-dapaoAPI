import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

/**
 * Dapao Template Manager v2.0
 * 
 * A visual template browser for the 333 GPT-4o prompt templates
 * Adapted from Tutu Template Manager
 */

// CSS loading state
let cssLoadAttempted = false;
let cssLoadSuccess = false;

/**
 * 获取扩展的基础路径（自动检测文件夹名称）
 */
function getExtensionBasePath() {
    // 方法1: 从当前脚本URL获取
    try {
        const scripts = document.querySelectorAll('script[src*="dapao_template_manager"]');
        if (scripts.length > 0) {
            const scriptUrl = scripts[0].src;
            // 提取 /extensions/XXX/ 部分
            const match = scriptUrl.match(/\/extensions\/([^/]+)\//);
            if (match) {
                return `/extensions/${match[1]}`;
            }
        }
    } catch (e) {
        console.warn("[Dapao CSS] Failed to get path from script tag:", e);
    }
    
    // 方法2: 尝试从已加载的CSS中获取
    try {
        const existingLinks = document.querySelectorAll('link[href*="dapao"]');
        for (const link of existingLinks) {
            const match = link.href.match(/\/extensions\/([^/]+)\//);
            if (match) {
                return `/extensions/${match[1]}`;
            }
        }
    } catch (e) {
        console.warn("[Dapao CSS] Failed to get path from existing links:", e);
    }
    
    return null;
}

/**
 * Enhanced CSS loading with multiple fallback strategies
 */
function ensureCssLoaded() {
    if (cssLoadAttempted) {
        console.log("[Dapao CSS] Already attempted to load CSS, success:", cssLoadSuccess);
        return;
    }
    
    cssLoadAttempted = true;
    console.log("[Dapao CSS] Starting CSS loading process...");
    
    // Check if CSS is already loaded
    const existingLinks = document.querySelectorAll('link[href*="dapao_styles.css"]');
    if (existingLinks.length > 0) {
        console.log("[Dapao CSS] ✅ CSS already loaded, found", existingLinks.length, "link(s)");
        cssLoadSuccess = true;
        return;
    }
    
    // 动态获取扩展路径
    const basePath = getExtensionBasePath();
    
    // 构建CSS路径列表
    const possibleFolderNames = [
        'ComfyUI-dapaoAPI',      // 标准名称
        'ComfyUI-dapaoAPI-main', // GitHub下载带后缀
        'ComfyUI-dapaoAPI-master'
    ];
    
    let cssPaths = [];
    
    if (basePath) {
        console.log("[Dapao CSS] Detected extension path:", basePath);
        cssPaths = [
            `${basePath}/css/dapao_styles.css`,
            `${basePath}/web/css/dapao_styles.css`
        ];
    } else {
        console.log("[Dapao CSS] Could not detect path, trying all possibilities...");
        for (const folderName of possibleFolderNames) {
            cssPaths.push(`/extensions/${folderName}/css/dapao_styles.css`);
            cssPaths.push(`/extensions/${folderName}/web/css/dapao_styles.css`);
        }
    }
    
    let loadedSuccessfully = false;
    
    cssPaths.forEach((cssPath, index) => {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.type = "text/css";
        link.href = cssPath;
        
        link.onload = () => {
            if (!loadedSuccessfully) {
                console.log(`[Dapao CSS] ✅ Successfully loaded CSS from: ${cssPath}`);
                cssLoadSuccess = true;
                loadedSuccessfully = true;
            }
        };
        
        link.onerror = () => {
            console.warn(`[Dapao CSS] ❌ Failed to load CSS from: ${cssPath}`);
            if (index === cssPaths.length - 1 && !loadedSuccessfully) {
                console.warn("[Dapao CSS] ⚠️ All CSS paths failed, injecting inline fallback styles...");
                injectFallbackStyles();
            }
        };
        
        console.log(`[Dapao CSS] Attempting to load CSS (path ${index + 1}/${cssPaths.length}): ${cssPath}`);
        document.head.appendChild(link);
    });
    
    // Set a timeout to check if CSS loaded
    setTimeout(() => {
        if (!cssLoadSuccess) {
            console.warn("[Dapao CSS] ⚠️ CSS loading timeout reached, injecting fallback styles...");
            injectFallbackStyles();
        }
    }, 2000);
}

/**
 * Inject minimal inline CSS as fallback
 */
function injectFallbackStyles() {
    const existingFallback = document.getElementById('dapao-fallback-styles');
    if (existingFallback) {
        console.log("[Dapao CSS] Fallback styles already injected");
        return;
    }
    
    const style = document.createElement("style");
    style.id = 'dapao-fallback-styles';
    style.textContent = `
        /* Dapao Template Manager - Fallback Styles */
        .dapao-modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 10000; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.8); }
        .dapao-modal-content { width: 90%; max-width: 1400px; height: 85%; max-height: 900px; background: #1e1e1e; border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; }
        .dapao-header { background: #2a2a2a; padding: 20px; border-bottom: 1px solid #3a3a3a; display: flex; align-items: center; gap: 20px; }
        .dapao-header h2 { margin: 0; color: #fff; flex: 1; }
        .close-btn { background: none; border: none; color: #fff; font-size: 24px; cursor: pointer; }
        .dapao-body { flex: 1; display: flex; overflow: hidden; }
        .dapao-sidebar { width: 280px; background: #252525; border-right: 1px solid #3a3a3a; display: flex; flex-direction: column; }
        .dapao-main { flex: 1; background: #1e1e1e; overflow-y: auto; padding: 25px; }
        .category-btn { width: 100%; background: #2a2a2a; border: 1px solid #3a3a3a; color: #fff; padding: 10px; margin: 5px; cursor: pointer; text-align: left; }
        .category-btn.active { background: #0066cc; }
        .template-item { background: #2a2a2a; border: 1px solid #3a3a3a; padding: 12px; margin: 8px; cursor: pointer; color: #fff; }
        .template-item.active { background: #0066cc; }
        .dapao-footer { background: #2a2a2a; padding: 15px; border-top: 1px solid #3a3a3a; display: flex; justify-content: flex-end; gap: 10px; }
        .dapao-footer button { padding: 10px 20px; border-radius: 6px; cursor: pointer; border: 1px solid #3a3a3a; }
        .btn-cancel { background: #3a3a3a; color: #fff; }
        .btn-apply { background: #0066cc; color: #fff; }
    `;
    document.head.appendChild(style);
    console.log("[Dapao CSS] ✅ Injected inline fallback styles");
}

// Global state
let dapaoTemplateState = {
    categories: [],
    currentCategory: null,
    currentTemplate: null,
    currentLang: 'zh',
    allTemplates: {},
    searchResults: []
};

/**
 * Create and open the template manager dialog
 */
function openTemplateManager(node) {
    console.log("[Dapao] Opening template manager for node:", node);
    
    // Ensure CSS is loaded before opening modal
    ensureCssLoaded();
    
    // Remove any existing modal
    const existingModal = document.getElementById('dapao-template-manager');
    if (existingModal) {
        console.log("[Dapao] Removing existing modal");
        existingModal.remove();
    }

    // Create modal
    const modal = createTemplateManagerModal(node);
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    
    console.log("[Dapao] Modal created and added to DOM");
    
    // Load data
    loadTemplateData(modal, node);
    
    // Show modal
    setTimeout(() => {
        modal.classList.add('dapao-modal-show');
        console.log("[Dapao] Modal displayed");
    }, 10);
}

/**
 * Create the template editor dialog (for create/edit)
 */
function createTemplateEditorDialog() {
    const dialog = document.createElement('div');
    dialog.className = 'dapao-modal dapao-editor-dialog';
    dialog.id = 'dapao-template-editor';
    dialog.innerHTML = `
        <div class="dapao-modal-overlay"></div>
        <div class="dapao-modal-content" style="max-width: 700px; height: auto; max-height: 85%;">
            <div class="dapao-header">
                <h2 class="editor-title">创建新模板</h2>
                <button class="close-btn">&times;</button>
            </div>
            
            <div class="dapao-body" style="padding: 25px; overflow-y: auto;">
                <form class="template-form">
                    <div class="form-group">
                        <label>标题 *</label>
                        <input type="text" name="title" required placeholder="请输入模板标题..." />
                    </div>
                    
                    <div class="form-group">
                        <label>分类</label>
                        <input type="text" name="category" placeholder="例如：肖像、标志、3D..." />
                    </div>
                    
                    <div class="form-group">
                        <label>描述（中文）</label>
                        <textarea name="description_zh" rows="3" placeholder="中文描述..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>描述（英文）</label>
                        <textarea name="description_en" rows="3" placeholder="英文描述..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>提示词（中文） *</label>
                        <textarea name="prompt_zh" rows="6" required placeholder="中文提示词..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>提示词（英文） *</label>
                        <textarea name="prompt_en" rows="6" required placeholder="英文提示词..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>标签（逗号分隔）</label>
                        <input type="text" name="tags" placeholder="标签1, 标签2, 标签3..." />
                    </div>
                    
                    <div class="form-group">
                        <label>缩略图 *</label>
                        <input type="text" name="coverImage" placeholder="输入图片URL 或 上传..." required />
                        
                        <div class="image-upload-controls" style="margin-top: 5px; display: flex; gap: 10px;">
                            <button type="button" class="btn-upload-image">📤 上传图片</button>
                            <button type="button" class="btn-use-generated">🖼️ 使用最后生成</button>
                            <input type="file" class="file-input-hidden" accept="image/*" style="display: none;" />
                        </div>
                        
                        <div class="image-preview" style="margin-top: 10px; display: none;">
                            <img src="" alt="Preview" style="max-width: 200px; max-height: 200px; border-radius: 4px;" />
                        </div>
                    </div>
                </form>
            </div>
            
            <div class="dapao-footer">
                <button class="btn-cancel">取消</button>
                <button class="btn-save">💾 保存模板</button>
            </div>
        </div>
    `;
    
    // Image Upload Logic
    const uploadBtn = dialog.querySelector('.btn-upload-image');
    const fileInput = dialog.querySelector('.file-input-hidden');
    const useGenBtn = dialog.querySelector('.btn-use-generated');
    const urlInput = dialog.querySelector('input[name="coverImage"]');
    const previewDiv = dialog.querySelector('.image-preview');
    const previewImg = previewDiv.querySelector('img');
    
    // Trigger file input
    uploadBtn.addEventListener('click', () => fileInput.click());
    
    // Handle File Selection
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('image', file);
        
        try {
            uploadBtn.textContent = '⏳ 上传中...';
            uploadBtn.disabled = true;
            
            const response = await api.fetchApi('/dapao/upload-image', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.url) {
                urlInput.value = result.url;
                previewImg.src = result.url;
                previewDiv.style.display = 'block';
                alert(`上传成功！大小: ${result.size_kb}KB`);
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (err) {
            alert('上传失败: ' + err.message);
        } finally {
            uploadBtn.textContent = '📤 上传图片';
            uploadBtn.disabled = false;
            fileInput.value = ''; // Reset
        }
    });
    
    // Handle Use Generated Image
    useGenBtn.addEventListener('click', async () => {
        try {
            useGenBtn.textContent = '⏳ 获取中...';
            useGenBtn.disabled = true;
            
            // 1. Get History
            const history = await api.getHistory(1);
            if (!history || !history.History || history.History.length === 0) {
                throw new Error('未找到生成历史');
            }
            
            const lastRun = history.History[0];
            const outputs = lastRun.outputs;
            
            // Find first image output
            let targetImage = null;
            for (const nodeId in outputs) {
                if (outputs[nodeId].images && outputs[nodeId].images.length > 0) {
                    targetImage = outputs[nodeId].images[0];
                    break;
                }
            }
            
            if (!targetImage) {
                throw new Error('最后一次运行没有生成图片');
            }
            
            // 2. Send to backend for processing
            const formData = new FormData();
            
            // Fix: Send as Blob with application/json type to ensure backend field.json() works correctly
            const jsonBlob = new Blob([JSON.stringify({
                filename: targetImage.filename,
                subfolder: targetImage.subfolder,
                type: targetImage.type
            })], { type: 'application/json' });
            
            formData.append('comfy_image', jsonBlob);
            
            const response = await api.fetchApi('/dapao/upload-image', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.url) {
                urlInput.value = result.url;
                previewImg.src = result.url;
                previewDiv.style.display = 'block';
                alert(`获取成功！大小: ${result.size_kb}KB`);
            } else {
                throw new Error(result.error || 'Processing failed');
            }
            
        } catch (err) {
            alert('获取图片失败: ' + err.message);
        } finally {
            useGenBtn.textContent = '🖼️ 使用最后生成';
            useGenBtn.disabled = false;
        }
    });
    
    // URL Input Change Preview
    urlInput.addEventListener('input', (e) => {
        if (e.target.value) {
            previewImg.src = e.target.value;
            previewDiv.style.display = 'block';
        } else {
            previewDiv.style.display = 'none';
        }
    });
    
    // If editing, show initial preview
    if (urlInput.value) {
        previewImg.src = urlInput.value;
        previewDiv.style.display = 'block';
    }

    return dialog;
}

/**
 * Create the main modal structure
 */
function createTemplateManagerModal(node) {
    const modal = document.createElement('div');
    modal.id = 'dapao-template-manager';
    modal.className = 'dapao-modal';
    modal.innerHTML = `
        <div class="dapao-modal-overlay"></div>
        <div class="dapao-modal-content">
            <!-- Header -->
            <div class="dapao-header">
                <h2>🎨 提示词模板管理器 <span class="template-count"></span></h2>
                <div class="dapao-controls">
                    <button class="lang-toggle active" data-lang="zh" style="display: none;">中文</button>
                    <button class="lang-toggle" data-lang="en" style="display: none;">English</button>
                    <input type="search" class="search-box" placeholder="搜索..." />
                </div>
                <button class="close-btn">&times;</button>
            </div>

            <!-- Body: Three-column layout -->
            <div class="dapao-body dapao-three-columns">
                <!-- Column 1: Categories -->
                <div class="dapao-column column-categories">
                    <h3 class="column-title">📁 分类</h3>
                    <div class="user-templates-section">
                        <button class="my-templates-btn">我的模板</button>
                        <button class="create-template-btn">创建新模板</button>
                    </div>
                    <div class="category-nav">
                        <div class="loading">加载中...</div>
                    </div>
                </div>

                <!-- Column 2: Template List -->
                <div class="dapao-column column-templates">
                    <h3 class="column-title">📋 模板列表</h3>
                    <div class="template-list">
                        <div class="info-message">← 请选择一个分类</div>
                    </div>
                </div>

                <!-- Column 3: Template Details -->
                <div class="dapao-column column-details">
                    <h3 class="column-title">📄 详情</h3>
                    <div class="detail-placeholder">
                        <p>← 请选择一个模板</p>
                    </div>
                    <div class="detail-content" style="display: none;">
                        <div class="detail-header">
                            <h3 class="template-title"></h3>
                            <div class="template-meta">
                                <span class="template-id"></span>
                                <span class="template-difficulty"></span>
                                <span class="template-source"></span>
                            </div>
                            <div class="template-actions" style="margin-top: 10px; display: none;">
                                <button class="btn-edit-template">✏️ 编辑</button>
                                <button class="btn-delete-template">🗑️ 删除</button>
                            </div>
                        </div>
                        
                        <div class="template-section">
                            <h4>描述</h4>
                            <div class="template-description"></div>
                        </div>
                        
                        <div class="template-section">
                            <h4>提示词</h4>
                            <div class="prompt-tabs">
                                <button class="tab-btn active" data-lang="zh">中文</button>
                                <button class="tab-btn" data-lang="en">English</button>
                            </div>
                            <textarea class="prompt-text" readonly></textarea>
                            <button class="copy-btn">📋 复制</button>
                        </div>

                        <div class="template-section">
                            <h4>📷 示例图片</h4>
                            <div class="images-gallery"></div>
                        </div>
                        
                        <div class="template-section">
                            <h4>🏷️ 标签</h4>
                            <div class="tags-list"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="dapao-footer">
                <button class="btn-cancel">关闭</button>
                <button class="btn-apply">✅ 应用模板</button>
            </div>
        </div>
    `;
    
    // Bind events
    bindModalEvents(modal, node);
    
    return modal;
}

/**
 * Load template data from backend
 */
async function loadTemplateData(modal, node) {
    try {
        console.log("[Dapao] Loading categories from API...");
        
        // Fetch categories in both languages
        const [categoriesZh, categoriesEn] = await Promise.all([
            api.fetchApi('/dapao/categories?lang=zh').then(r => r.json()),
            api.fetchApi('/dapao/categories?lang=en').then(r => r.json())
        ]);
        
        console.log("[Dapao] Loaded categories (zh):", categoriesZh);
        console.log("[Dapao] Loaded categories (en):", categoriesEn);
        
        // Merge bilingual data
        const categories = categoriesZh.map((catZh, index) => ({
            id: catZh.id,
            nameZh: catZh.name,
            nameEn: categoriesEn[index]?.name || catZh.name,
            count: catZh.count
        }));
        
        if (!categories || categories.length === 0) {
            throw new Error("No categories found");
        }
        
        dapaoTemplateState.categories = categories;
        
        // Render categories
        renderCategories(modal, categories);
        
        // Update count
        modal.querySelector('.template-count').textContent = `（333 个模板，${categories.length} 个分类）`;
        
        console.log("[Dapao] Successfully loaded", categories.length, "categories");
        
    } catch (error) {
        console.error("[Dapao] Failed to load template data:", error);
        console.error("[Dapao] Error stack:", error.stack);
        alert(`加载模板数据失败：\n${error.message}\n\n请检查浏览器控制台获取详细信息。`);
    }
}

/**
 * Render category buttons
 */
function renderCategories(modal, categories) {
    const nav = modal.querySelector('.category-nav');
    nav.innerHTML = '';
    
    categories.forEach((cat, index) => {
        const btn = document.createElement('button');
        btn.className = 'category-btn' + (index === 0 ? ' active' : '');
        btn.dataset.categoryId = cat.id;
        btn.innerHTML = `
            <span class="cat-name">${cat.nameZh}</span>
            <span class="cat-count">${cat.count}</span>
        `;
        
        btn.addEventListener('click', () => {
            // Update active state
            nav.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Load templates for this category
            loadCategoryTemplates(modal, cat);
        });
        
        nav.appendChild(btn);
    });
    
    // Auto-load first category
    if (categories.length > 0) {
        loadCategoryTemplates(modal, categories[0]);
    }
}

/**
 * Load templates for a specific category
 */
async function loadCategoryTemplates(modal, category) {
    const list = modal.querySelector('.template-list');
    list.innerHTML = '<div class="loading">加载模板中...</div>';
    
    dapaoTemplateState.currentCategory = category;
    
    try {
        const lang = dapaoTemplateState.currentLang;
        const categoryKey = category.id; 

        const response = await api.fetchApi(`/dapao/templates?category=${categoryKey}&lang=${lang}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.error}`);
        }
        const templates = await response.json();
        
        // Store templates under the original category ID
        dapaoTemplateState.allTemplates[category.id] = templates;
        renderTemplateList(modal, templates);
        
    } catch (error) {
        console.error(`[Dapao] Failed to load templates for category: ${category.nameEn}`, error);
        list.innerHTML = `<div class="info-message error">加载模板失败。错误：${error.message}</div>`;
    }
    
    console.log("[Dapao] Category selected:", category);
}

function renderTemplateList(modal, templates) {
    const list = modal.querySelector('.template-list');
    if (!templates || templates.length === 0) {
        list.innerHTML = `<div class="info-message">此分类中未找到模板。</div>`;
        return;
    }
    
    list.innerHTML = templates.map(tpl => `
        <div class="template-item" data-template-id="${tpl.id}">
            <div class="template-item-title">${tpl.title}</div>
            <div class="template-item-meta">
                <span>ID: ${tpl.id}</span>
            </div>
        </div>
    `).join('');
    
    // Add click event to each item
    list.querySelectorAll('.template-item').forEach(item => {
        item.addEventListener('click', () => {
            list.querySelectorAll('.template-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            const templateIdStr = item.dataset.templateId;
            const templateIdNum = parseInt(templateIdStr, 10);
            let template = null;
            
            // 优先从传入的模板数组中查找
            template = templates.find(t => t.id === templateIdStr || t.id === templateIdNum);
            
            // 如果没找到，尝试从所有已加载的分类中查找
            if (!template) {
                for (const categoryId in dapaoTemplateState.allTemplates) {
                    const categoryTemplates = dapaoTemplateState.allTemplates[categoryId];
                    template = categoryTemplates.find(t => t.id === templateIdStr || t.id === templateIdNum);
                    if (template) {
                        break;
                    }
                }
            }
            
            if (template) {
                renderTemplateDetail(modal, template);
            } else {
                console.error("[Dapao] Template not found:", templateIdStr);
            }
        });
    });
}

function renderTemplateDetail(modal, template) {
    dapaoTemplateState.currentTemplate = template;
    
    const detailContent = modal.querySelector('.detail-content');
    modal.querySelector('.detail-placeholder').style.display = 'none';
    detailContent.style.display = 'block';
    
    // Header
    detailContent.querySelector('.template-title').textContent = template.title;
    detailContent.querySelector('.template-id').textContent = `ID：${template.id}`;
    
    // 难度字段
    const difficultyEl = detailContent.querySelector('.template-difficulty');
    if (template.difficulty && template.difficulty.trim()) {
        difficultyEl.textContent = `难度：${template.difficulty}`;
        difficultyEl.style.display = 'inline';
    } else {
        difficultyEl.style.display = 'none';
    }
    
    // Source
    const sourceEl = detailContent.querySelector('.template-source');
    if (template.source && template.source.name) {
        sourceEl.textContent = `来源：${template.source.name}`;
        if (template.source.url) {
            sourceEl.innerHTML = `来源：<a href="${template.source.url}" target="_blank" rel="noopener">${template.source.name}</a>`;
        }
        sourceEl.style.display = 'inline';
    } else {
        sourceEl.style.display = 'none';
    }
    
    // Show/hide edit/delete buttons for user templates
    const templateActions = detailContent.querySelector('.template-actions');
    const isUserTemplate = typeof template.id === 'string' && template.id.startsWith('user_');
    if (isUserTemplate) {
        templateActions.style.display = 'flex';
    } else {
        templateActions.style.display = 'none';
    }
    
    // Description
    const lang = dapaoTemplateState.currentLang;
    const descEl = detailContent.querySelector('.template-description');
    
    let descriptionText = '';
    if (template.description) {
        if (typeof template.description === 'string') {
            descriptionText = template.description.trim();
        } else if (typeof template.description === 'object' && template.description[lang]) {
            descriptionText = template.description[lang].trim();
        }
    }
    
    const descSection = descEl.closest('.template-section');
    if (descriptionText) {
        descEl.textContent = descriptionText;
        if (descSection) descSection.style.display = 'block';
    } else {
        descEl.textContent = '';
        if (descSection) descSection.style.display = 'none';
    }
    
    // Prompt
    const activePromptLang = modal.querySelector('.prompt-tabs .tab-btn.active')?.dataset?.lang || 'zh';
    detailContent.querySelector('.prompt-text').value = template.prompt[activePromptLang] || '';
    
    // Images
    const gallery = detailContent.querySelector('.images-gallery');
    if (template.images && template.images.length > 0) {
        gallery.innerHTML = template.images.map((img, index) => {
            // Use the custom image API endpoint
            const filename = img.split('/').pop();
            let imageUrl = '';
            if (img.startsWith('/dapao/user-assets/')) {
                imageUrl = img;
            } else if (img.startsWith('/dapao/images/')) {
                imageUrl = img;
            } else if (img.startsWith('images/')) {
                 imageUrl = `/dapao/images/${filename}`;
            } else {
                 imageUrl = img;
            }
            return `<img src="${imageUrl}" alt="Example" class="image-thumb" data-image-index="${index}" data-image-url="${imageUrl}" onerror="console.error('Failed to load image:', this.src)" />`;
        }).join('');
        
        // Add double-click event listeners to images
        gallery.querySelectorAll('.image-thumb').forEach(img => {
            img.addEventListener('dblclick', () => {
                const imageUrl = img.dataset.imageUrl;
                const allImages = Array.from(gallery.querySelectorAll('.image-thumb')).map(i => i.dataset.imageUrl);
                const currentIndex = parseInt(img.dataset.imageIndex);
                openImageViewer(imageUrl, allImages, currentIndex);
            });
        });
    } else {
        gallery.innerHTML = '<span>暂无示例图片。</span>';
    }
    
    // Tags
    const tagsList = detailContent.querySelector('.tags-list');
    if (template.tags && template.tags.length > 0) {
        tagsList.innerHTML = template.tags.map(t => `<span class="tag">${t}</span>`).join('');
    } else {
        tagsList.innerHTML = '<span>暂无标签。</span>';
    }
}

/**
 * Load user templates
 */
async function loadUserTemplates(modal) {
    const list = modal.querySelector('.template-list');
    list.innerHTML = '<div class="loading">加载用户模板中...</div>';
    
    try {
        const response = await api.fetchApi('/dapao/user-templates');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const userTemplates = await response.json();
        
        console.log("[Dapao] Loaded user templates:", userTemplates);
        
        // Store in state
        dapaoTemplateState.allTemplates['user_custom'] = userTemplates;
        dapaoTemplateState.currentCategory = { id: 'user_custom', nameZh: '我的模板', nameEn: 'My Templates' };
        
        // Render
        if (userTemplates.length === 0) {
            list.innerHTML = `
                <div class="info-message">
                    <p><strong>还没有自定义模板</strong></p>
                    <p>点击"创建新模板"添加您的第一个模板！</p>
                </div>
            `;
        } else {
            renderTemplateList(modal, userTemplates);
        }
        
    } catch (error) {
        console.error("[Dapao] Failed to load user templates:", error);
        list.innerHTML = `<div class="info-message error">加载用户模板失败：${error.message}</div>`;
    }
}

/**
 * Open template editor (create or edit mode)
 */
function openTemplateEditor(modal, template = null) {
    const isEditMode = !!template;
    
    // Create editor dialog
    const editor = createTemplateEditorDialog();
    document.body.appendChild(editor);
    
    // Set title
    editor.querySelector('.editor-title').textContent = isEditMode ? '编辑模板' : '创建新模板';
    
    // Fill form if editing
    if (isEditMode) {
        const form = editor.querySelector('.template-form');
        form.querySelector('[name="title"]').value = template.title || '';
        form.querySelector('[name="category"]').value = template.category || '';
        form.querySelector('[name="description_zh"]').value = template.description?.zh || '';
        form.querySelector('[name="description_en"]').value = template.description?.en || '';
        form.querySelector('[name="prompt_zh"]').value = template.prompt?.zh || '';
        form.querySelector('[name="prompt_en"]').value = template.prompt?.en || '';
        form.querySelector('[name="tags"]').value = template.tags ? template.tags.join(', ') : '';
        form.querySelector('[name="coverImage"]').value = template.coverImage || '';
        
        if (template.coverImage) {
            const previewImg = editor.querySelector('.image-preview img');
            const previewDiv = editor.querySelector('.image-preview');
            previewImg.src = template.coverImage;
            previewDiv.style.display = 'block';
        }
    }
    
    // Bind events
    editor.querySelector('.close-btn').addEventListener('click', () => {
        editor.remove();
    });
    
    editor.querySelector('.btn-cancel').addEventListener('click', () => {
        editor.remove();
    });
    
    editor.querySelector('.btn-save').addEventListener('click', async () => {
        const form = editor.querySelector('.template-form');
        const formData = new FormData(form);
        
        // Validate required fields
        if (!formData.get('title') || !formData.get('prompt_zh') || !formData.get('prompt_en')) {
            alert('请填写所有必填字段（标题、中文提示词、英文提示词）');
            return;
        }
        
        // Prepare data
        const data = {
            title: formData.get('title'),
            category: formData.get('category') || 'custom',
            description_zh: formData.get('description_zh'),
            description_en: formData.get('description_en'),
            prompt_zh: formData.get('prompt_zh'),
            prompt_en: formData.get('prompt_en'),
            tags: formData.get('tags') ? formData.get('tags').split(',').map(t => t.trim()).filter(t => t) : ['custom']
        };
        
        try {
            let response;
            if (isEditMode) {
                // Update existing template
                response = await api.fetchApi(`/dapao/user-templates/${template.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } else {
                // Create new template
                response = await api.fetchApi('/dapao/user-templates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            }
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || '保存模板失败');
            }
            
            const result = await response.json();
            console.log("[Dapao] Template saved:", result);
            
            // Close editor
            editor.remove();
            
            // Reload user templates
            loadUserTemplates(modal);
            
            // Show success message
            alert(isEditMode ? '模板更新成功！' : '模板创建成功！');
            
        } catch (error) {
            console.error("[Dapao] Failed to save template:", error);
            alert(`保存模板失败：${error.message}`);
        }
    });
    
    // Show editor
    editor.style.display = 'flex';
    setTimeout(() => {
        editor.classList.add('dapao-modal-show');
    }, 10);
}

/**
 * Delete a user template
 */
async function deleteUserTemplate(modal, template) {
    if (!confirm(`确定要删除"${template.title}"吗？\n\n此操作无法撤销。`)) {
        return;
    }
    
    try {
        const response = await api.fetchApi(`/dapao/user-templates/${template.id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete template');
        }
        
        console.log("[Dapao] Template deleted:", template.id);
        
        // Reload user templates
        loadUserTemplates(modal);
        
        // Clear detail view
        modal.querySelector('.detail-placeholder').style.display = 'flex';
        modal.querySelector('.detail-content').style.display = 'none';
        
        alert('模板删除成功！');
        
    } catch (error) {
        console.error("[Dapao] Failed to delete template:", error);
        alert(`删除模板失败：${error.message}`);
    }
}

/**
 * Bind all modal events
 */
function bindModalEvents(modal, node) {
    // Close button
    modal.querySelector('.close-btn').addEventListener('click', () => {
        closeModal(modal);
    });
    
    modal.querySelector('.btn-cancel').addEventListener('click', () => {
        closeModal(modal);
    });
    
    // Click overlay to close
    modal.querySelector('.dapao-modal-overlay').addEventListener('click', () => {
        closeModal(modal);
    });
    
    // Apply button
    modal.querySelector('.btn-apply').addEventListener('click', () => {
        applyTemplate(modal, node);
    });
    
    // My Templates button
    modal.querySelector('.my-templates-btn').addEventListener('click', () => {
        loadUserTemplates(modal);
    });
    
    // Create New button
    modal.querySelector('.create-template-btn').addEventListener('click', () => {
        openTemplateEditor(modal);
    });
    
    // Edit template button
    modal.querySelector('.btn-edit-template').addEventListener('click', () => {
        const template = dapaoTemplateState.currentTemplate;
        if (template) {
            openTemplateEditor(modal, template);
        }
    });
    
    // Delete template button
    modal.querySelector('.btn-delete-template').addEventListener('click', () => {
        const template = dapaoTemplateState.currentTemplate;
        if (template) {
            deleteUserTemplate(modal, template);
        }
    });
    
    // Language toggle
    modal.querySelectorAll('.lang-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            modal.querySelectorAll('.lang-toggle').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            dapaoTemplateState.currentLang = btn.dataset.lang;
            updateLanguage(modal);
        });
    });
    
    // Prompt language tabs
    modal.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            modal.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            switchPromptLanguage(modal, btn.dataset.lang);
        });
    });
    
    // Copy button
    modal.querySelector('.copy-btn').addEventListener('click', () => {
        const promptText = modal.querySelector('.prompt-text');
        promptText.select();
        document.execCommand('copy');
        
        const btn = modal.querySelector('.copy-btn');
        btn.textContent = '✅ 已复制！';
        setTimeout(() => {
            btn.textContent = '📋 复制';
        }, 2000);
    });
    
    // Search
    const searchBox = modal.querySelector('.search-box');
    searchBox.addEventListener('input', debounce((e) => {
        searchTemplates(modal, e.target.value);
    }, 300));
}

/**
 * Open image viewer modal for full-size image viewing
 */
function openImageViewer(imageUrl, allImages = [], currentIndex = 0) {
    // Remove any existing image viewer
    const existingViewer = document.getElementById('dapao-image-viewer');
    if (existingViewer) {
        existingViewer.remove();
    }
    
    // Ensure allImages has at least the current image
    if (!allImages || allImages.length === 0) {
        allImages = [imageUrl];
        currentIndex = 0;
    }
    
    // Ensure currentIndex is valid
    if (currentIndex < 0 || currentIndex >= allImages.length) {
        currentIndex = 0;
    }
    
    // Use the imageUrl from allImages if available
    const displayImageUrl = allImages[currentIndex] || imageUrl;
    
    // Create image viewer modal
    const viewer = document.createElement('div');
    viewer.id = 'dapao-image-viewer';
    viewer.className = 'dapao-modal dapao-image-viewer';
    viewer.innerHTML = `
        <div class="dapao-modal-overlay"></div>
        <div class="dapao-modal-content image-viewer-content">
            <div class="image-viewer-header">
                <div class="image-viewer-title">
                    <span class="image-counter">${currentIndex + 1} / ${allImages.length}</span>
                </div>
                <button class="close-btn">&times;</button>
            </div>
            <div class="image-viewer-body">
                <button class="image-nav-btn image-nav-prev" ${currentIndex === 0 || allImages.length <= 1 ? 'disabled' : ''}>‹</button>
                <div class="image-container">
                    <img src="${displayImageUrl}" alt="Full size image" class="full-size-image" />
                    <div class="image-loading">加载中...</div>
                </div>
                <button class="image-nav-btn image-nav-next" ${currentIndex === allImages.length - 1 || allImages.length <= 1 ? 'disabled' : ''}>›</button>
            </div>
            <div class="image-viewer-footer">
                <button class="btn-close-viewer">关闭</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(viewer);
    
    let currentImgIndex = currentIndex;
    const imageElement = viewer.querySelector('.full-size-image');
    const counterElement = viewer.querySelector('.image-counter');
    const prevBtn = viewer.querySelector('.image-nav-prev');
    const nextBtn = viewer.querySelector('.image-nav-next');
    const loadingElement = viewer.querySelector('.image-loading');
    
    // Show loading state
    const showLoading = () => {
        loadingElement.style.display = 'block';
        imageElement.style.opacity = '0.3';
    };
    
    // Hide loading state
    const hideLoading = () => {
        loadingElement.style.display = 'none';
        imageElement.style.opacity = '1';
    };
    
    // Load image
    const loadImage = (index) => {
        if (index < 0 || index >= allImages.length || allImages.length <= 1) return;
        
        currentImgIndex = index;
        const newImageUrl = allImages[index];
        
        showLoading();
        imageElement.src = newImageUrl;
        counterElement.textContent = `${index + 1} / ${allImages.length}`;
        
        // Update navigation buttons
        prevBtn.disabled = index === 0;
        nextBtn.disabled = index === allImages.length - 1;
        
        // Image load event
        imageElement.onload = () => {
            hideLoading();
        };
        
        imageElement.onerror = () => {
            hideLoading();
            console.error('Failed to load image:', newImageUrl);
        };
    };
    
    // Navigation (only if multiple images)
    if (allImages.length > 1) {
        prevBtn.addEventListener('click', () => {
            if (currentImgIndex > 0) {
                loadImage(currentImgIndex - 1);
            }
        });
        
        nextBtn.addEventListener('click', () => {
            if (currentImgIndex < allImages.length - 1) {
                loadImage(currentImgIndex + 1);
            }
        });
        
        // Keyboard navigation
        const handleKeyPress = (e) => {
            if (e.key === 'ArrowLeft' && currentImgIndex > 0) {
                loadImage(currentImgIndex - 1);
            } else if (e.key === 'ArrowRight' && currentImgIndex < allImages.length - 1) {
                loadImage(currentImgIndex + 1);
            } else if (e.key === 'Escape') {
                closeImageViewer(viewer);
            }
        };
        
        document.addEventListener('keydown', handleKeyPress);
        viewer._keyHandler = handleKeyPress; // Store reference for cleanup
    } else {
        // Single image - only ESC key to close
        const handleKeyPress = (e) => {
            if (e.key === 'Escape') {
                closeImageViewer(viewer);
            }
        };
        document.addEventListener('keydown', handleKeyPress);
        viewer._keyHandler = handleKeyPress;
    }
    
    // Close handlers
    const closeHandler = () => {
        if (viewer._keyHandler) {
            document.removeEventListener('keydown', viewer._keyHandler);
        }
        closeImageViewer(viewer);
    };
    
    viewer.querySelector('.close-btn').addEventListener('click', closeHandler);
    viewer.querySelector('.btn-close-viewer').addEventListener('click', closeHandler);
    viewer.querySelector('.dapao-modal-overlay').addEventListener('click', closeHandler);
    
    // Show viewer
    viewer.style.display = 'flex';
    setTimeout(() => {
        viewer.classList.add('dapao-modal-show');
    }, 10);
    
    // Initial load
    imageElement.onload = () => {
        hideLoading();
    };
    imageElement.onerror = () => {
        hideLoading();
        console.error('Failed to load image:', displayImageUrl);
    };
}

/**
 * Close image viewer
 */
function closeImageViewer(viewer) {
    if (viewer._keyHandler) {
        document.removeEventListener('keydown', viewer._keyHandler);
    }
    viewer.classList.remove('dapao-modal-show');
    setTimeout(() => {
        viewer.remove();
    }, 300);
}

/**
 * Close modal with animation
 */
function closeModal(modal) {
    modal.classList.remove('dapao-modal-show');
    setTimeout(() => {
        modal.remove();
    }, 300);
}

/**
 * Apply selected template to node
 */
function applyTemplate(modal, node) {
    const template = dapaoTemplateState.currentTemplate;
    
    if (!template) {
        alert('请先选择一个模板');
        return;
    }
    
    // Get the currently active language tab (zh or en)
    const activePromptLang = modal.querySelector('.prompt-tabs .tab-btn.active')?.dataset?.lang || 'zh';
    const promptText = template.prompt[activePromptLang];
    
    if (!promptText) {
        alert('所选语言的提示词文本不可用');
        return;
    }
    
    // Find the prompt widget
    const promptWidget = node.widgets?.find(w => w.name === 'prompt');
    
    if (!promptWidget) {
        alert('节点中未找到提示词组件');
        return;
    }
    
    // Append the prompt text to the existing content
    const currentValue = promptWidget.value || '';
    const separator = currentValue.trim() ? '\n\n' : '';
    promptWidget.value = currentValue + separator + promptText;
    
    // Update the input element if it exists
    if (promptWidget.inputEl) {
        promptWidget.inputEl.value = promptWidget.value;
    }
    
    // Close modal
    closeModal(modal);
    
    // Notify user
    const langName = activePromptLang === 'zh' ? '中文' : '英文';
    const message = `✅ 模板已应用！\n\n模板：${template.title}\n语言：${langName}\n\n提示词已添加到输入框中。`;
    console.log("[Dapao]", message);
    
    // Use ComfyUI's dialog if available, otherwise use alert
    if (app.ui?.dialog?.show) {
        app.ui.dialog.show(message);
    } else {
        alert(message);
    }
    
    console.log("[Dapao] Applied template:", template.id, "in", langName);
}

/**
 * Debounce helper
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Update UI language
 */
function updateLanguage(modal) {
    // Update category names
    const lang = dapaoTemplateState.currentLang;
    modal.querySelectorAll('.category-btn').forEach((btn, index) => {
        const cat = dapaoTemplateState.categories[index];
        if (cat) {
            btn.querySelector('.cat-name').textContent = lang === 'zh' ? cat.nameZh : cat.nameEn;
        }
    });
}

/**
 * Switch prompt display language
 */
function switchPromptLanguage(modal, lang) {
    const template = dapaoTemplateState.currentTemplate;
    if (template && template.prompt) {
        modal.querySelector('.prompt-text').value = template.prompt[lang] || template.prompt.en;
    }
}

/**
 * Search templates across all categories
 */
async function searchTemplates(modal, keyword) {
    const list = modal.querySelector('.template-list');
    
    if (!keyword.trim()) {
        // Clear search, restore current category view
        if (dapaoTemplateState.currentCategory) {
            const templates = dapaoTemplateState.allTemplates[dapaoTemplateState.currentCategory.id];
            if (templates) {
                renderTemplateList(modal, templates);
            }
        }
        return;
    }
    
    console.log("[Dapao] Searching for:", keyword);
    
    // Show loading
    list.innerHTML = '<div class="loading">搜索中...</div>';
    
    try {
        // Collect all templates from all loaded categories
        let allTemplates = [];
        for (const categoryId in dapaoTemplateState.allTemplates) {
            const templates = dapaoTemplateState.allTemplates[categoryId];
            allTemplates = allTemplates.concat(templates);
        }
        
        // If no templates are loaded yet, we need to load them first
        if (allTemplates.length === 0) {
            list.innerHTML = '<div class="info-message">请先选择一个分类以加载模板。</div>';
            return;
        }
        
        // Search in title, description, and tags (case-insensitive)
        const searchLower = keyword.toLowerCase();
        const results = allTemplates.filter(template => {
            // Search in title
            if (template.title && template.title.toLowerCase().includes(searchLower)) {
                return true;
            }
            
            // Search in description (both languages)
            if (template.description) {
                if (template.description.zh && template.description.zh.toLowerCase().includes(searchLower)) {
                    return true;
                }
                if (template.description.en && template.description.en.toLowerCase().includes(searchLower)) {
                    return true;
                }
            }
            
            // Search in tags
            if (template.tags && Array.isArray(template.tags)) {
                if (template.tags.some(tag => tag.toLowerCase().includes(searchLower))) {
                    return true;
                }
            }
            
            // Search in prompt text (both languages)
            if (template.prompt) {
                if (template.prompt.zh && template.prompt.zh.toLowerCase().includes(searchLower)) {
                    return true;
                }
                if (template.prompt.en && template.prompt.en.toLowerCase().includes(searchLower)) {
                    return true;
                }
            }
            
            return false;
        });
        
        console.log(`[Dapao] Found ${results.length} results for "${keyword}"`);
        
        // Display results
        if (results.length === 0) {
            list.innerHTML = `
                <div class="info-message">
                    <p><strong>未找到结果</strong></p>
                    <p>请尝试其他关键词或按分类浏览。</p>
                </div>
            `;
        } else {
            // Render search results
            renderTemplateList(modal, results);
            
            // Add search header
            const searchHeader = document.createElement('div');
            searchHeader.className = 'search-header';
            searchHeader.innerHTML = `
                <div style="padding: 10px; background: #2a2a2a; border-bottom: 1px solid #3a3a3a; color: #aaa; font-size: 13px;">
                    找到 ${results.length} 个结果，关键词："${keyword}"
                </div>
            `;
            list.insertBefore(searchHeader, list.firstChild);
        }
        
    } catch (error) {
        console.error("[Dapao] Search error:", error);
        list.innerHTML = `<div class="info-message error">搜索失败：${error.message}</div>`;
    }
}


/**
 * Set random prompt to the node
 */
async function setRandomPrompt(node, tag = null) {
    try {
        const promptWidget = node.widgets.find(w => w.name === "prompt" || w.type === "customtext" || w.type === "STRING");
        if (!promptWidget) {
            alert("找不到提示词输入框");
            return;
        }
        
        // Fetch templates if not loaded
        let templates = [];
        // Check if dapaoTemplateState is available (it might be defined in this file's scope or window)
        // If not available, we fetch directly.
        if (typeof dapaoTemplateState !== 'undefined' && dapaoTemplateState.allTemplates && dapaoTemplateState.allTemplates['text_to_image']) {
            templates = dapaoTemplateState.allTemplates['text_to_image'];
        }
        
        if (!templates || templates.length === 0) {
             const response = await api.fetchApi('/dapao/templates?category=text_to_image&lang=zh');
             if (response.ok) {
                 templates = await response.json();
                 // Cache it if possible
                 if (typeof dapaoTemplateState !== 'undefined') {
                     if (!dapaoTemplateState.allTemplates) dapaoTemplateState.allTemplates = {};
                     dapaoTemplateState.allTemplates['text_to_image'] = templates;
                 }
             }
        }
        
        if (!templates || templates.length === 0) {
            alert("未找到模板数据");
            return;
        }
        
        // Filter by tag
        let candidates = templates;
        if (tag) {
            candidates = templates.filter(t => t.tags && t.tags.includes(tag));
        }
        
        if (candidates.length === 0) {
            alert(`未找到标签为 "${tag}" 的模板`);
            return;
        }
        
        // Pick random
        const randomTemplate = candidates[Math.floor(Math.random() * candidates.length)];
        
        // Extract prompt text
        let promptText = "";
        if (randomTemplate.prompts && Array.isArray(randomTemplate.prompts) && randomTemplate.prompts.length > 0) {
             promptText = randomTemplate.prompts[0];
        } else if (randomTemplate.prompt) {
             promptText = typeof randomTemplate.prompt === 'string' ? randomTemplate.prompt : (randomTemplate.prompt.en || randomTemplate.prompt.zh);
        }
        
        if (promptText) {
            promptWidget.value = promptText;
            node.setDirtyCanvas(true, true); 
        }
        
    } catch (e) {
        console.error("[Dapao] Error setting random prompt:", e);
        alert("随机提示词出错: " + e.message);
    }
}

// ======================== Extension Registration ========================

app.registerExtension({
    name: "Dapao.TemplateManagerV2",
    
    async setup() {
        // Pre-load CSS when extension initializes
        console.log("[Dapao] Extension setup - Pre-loading CSS...");
        ensureCssLoaded();
    },
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "DapaoPromptNode") {
            const onAdded = nodeType.prototype.onAdded;
            nodeType.prototype.onAdded = function() {
                onAdded?.apply(this, arguments);

                // Set a comfortable default size for the simplified node
                const minWidth = 480;
                const minHeight = 500; // Increased height for new buttons

                if (this.size[0] < minWidth) {
                    this.size[0] = minWidth;
                }
                if (this.size[1] < minHeight) {
                    this.size[1] = minHeight;
                }
                
                // Add the Browse Templates button if it doesn't exist
                const hasButton = this.widgets && this.widgets.find(w => w.name === "浏览模板");
                if (!hasButton) {
                    this.addWidget("button", "浏览模板", null, () => {
                        openTemplateManager(this);
                    });
                    
                    // Add Random Buttons
                    // 1. Random All
                    this.addWidget("button", "🎲 随机一个提示词 (全部)", null, () => setRandomPrompt(this));
                    
                    // 2. Random Categories (Stacked due to LiteGraph limitations, representing the grid)
                    this.addWidget("button", "👤 随机人物类提示词", null, () => setRandomPrompt(this, "portrait"));
                    this.addWidget("button", "🏞️ 随机风景类提示词", null, () => setRandomPrompt(this, "landscape"));
                    this.addWidget("button", "📷 随机摄影类提示词", null, () => setRandomPrompt(this, "photography"));
                    this.addWidget("button", "🎨 随机极简类提示词", null, () => setRandomPrompt(this, "minimalist"));
                }
                
                this.setDirtyCanvas(true, true);
            };
        }
    },

    async getExtraMenuOptions(graphCanvas, node) {
        if (node.type !== "DapaoPromptNode") {
            return;
        }
        // No additional menu options needed for the simplified version
    }
});

console.log("[Dapao] Template Manager extension v2 loaded");
