/**
 * Brand Registration Client-side JavaScript
 * Handles communication between the frontend form and backend API
 */

class BrandRegistrationClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.apiBase = `${baseUrl}/api/v1/brands`;
    }

    /**
     * Upload brand guideline document
     */
    async uploadGuideline(brandId, file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Note: v1 API has a generic /upload endpoint
            const response = await fetch(`${this.apiBase}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Upload error:', error);
            throw error;
        }
    }

    /**
     * Save brand settings/blueprint (voice, pillars, policies)
     * Backend uses a single PUT /{brand_id}/blueprint endpoint
     */
    async saveBlueprint(brandId, blueprint) {
        try {
            const response = await fetch(`${this.apiBase}/${brandId}/blueprint`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(blueprint)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save blueprint');
            }

            return await response.json();
        } catch (error) {
            console.error('Blueprint save error:', error);
            throw error;
        }
    }

    /**
     * Alias for saveBlueprint to maintain compatibility
     */
    async saveSettings(brandId, settings) {
        return this.saveBlueprint(brandId, settings);
    }

    /**
     * Get brand data
     */
    async getBrand(brandId) {
        try {
            const response = await fetch(`${this.apiBase}/${brandId}`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to get brand data');
            }

            return await response.json();
        } catch (error) {
            console.error('Get brand error:', error);
            throw error;
        }
    }

    /**
     * List all brands
     */
    async listBrands() {
        try {
            const response = await fetch(`${this.apiBase}/`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to list brands');
            }

            return await response.json();
        } catch (error) {
            console.error('List brands error:', error);
            throw error;
        }
    }

    /**
     * Create new brand (Register)
     */
    async createBrand(brandData) {
        try {
            const response = await fetch(`${this.apiBase}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(brandData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create brand');
            }

            return await response.json();
        } catch (error) {
            console.error('Create brand error:', error);
            throw error;
        }
    }

    /**
     * Update brand data
     */
    async updateBrand(brandId, updates) {
        try {
            const response = await fetch(`${this.apiBase}/update-brand/${brandId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update brand');
            }

            return await response.json();
        } catch (error) {
            console.error('Update brand error:', error);
            throw error;
        }
    }
}

/**
 * Enhanced Brand Content System with Backend Integration
 */
function enhancedBrandContentSystem() {
    const client = new BrandRegistrationClient();

    return {
        // ... existing properties from original function
        activeTab: 'onboarding',
        isGeneratingPlan: false,
        isGeneratingBlueprint: false,
        isRegenerating: false,

        // Brand data
        brand: {
            id: 'brand-001',
            name: 'TechBrand',
            guidelineDoc: { name: '', size: 0, status: 'none' },
            blueprint: {
                version: '1.0.0',
                status: 'draft',
                voice: {
                    formality: 30,
                    humor: 60,
                    warmth: 70,
                    emojiPolicy: 'medium'
                },
                pillars: [
                    { name: 'Innovation', description: 'Latest tech trends and breakthroughs', weight: 30 },
                    { name: 'Education', description: 'Teaching and learning content', weight: 25 },
                    { name: 'Community', description: 'Building connections and engagement', weight: 25 },
                    { name: 'Product', description: 'Product features and benefits', weight: 20 }
                ],
                policies: {
                    forbiddenPhrases: ['buy now', 'limited time', 'act fast'],
                    maxHashtags: 5,
                    brandHashtags: ['#TechBrand', '#Innovation', '#AI']
                },
                productDefaultPct: 30
            }
        },

        // Settings
        settings: {
            defaultLanguage: 'en',
            defaultLLM: 'gpt-4.1',
            productDefaultPct: 30
        },

        // UI state
        newForbiddenPhrase: '',
        newBrandHashtag: '',
        guidelineDoc: { name: '', status: 'none' },
        isUploading: false,
        isSaving: false,

        // Initialize
        async init() {
            // Try to load existing brand data
            try {
                const brandData = await client.getBrand(this.brand.id);
                this.brand = { ...this.brand, ...brandData };
                this.settings = { ...this.settings, ...brandData.settings };
            } catch (error) {
                console.log('No existing brand data found, using defaults');
            }
        },

        /**
         * Handle file upload with backend integration
         */
        async handleGuidelineUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            // Validate file
            const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
            if (!allowedTypes.includes(file.type)) {
                alert('Please upload only PDF or DOCX files');
                return;
            }

            if (file.size > 50 * 1024 * 1024) {
                alert('File size must be less than 50MB');
                return;
            }

            this.isUploading = true;
            this.guidelineDoc = {
                name: file.name,
                size: file.size,
                status: 'uploading'
            };

            try {
                const result = await client.uploadGuideline(this.brand.id, file);

                this.guidelineDoc = {
                    name: result.original_name,
                    size: result.size,
                    status: 'uploaded'
                };

                // Update brand data with file details
                this.brand.guidelineDoc = {
                    ...this.guidelineDoc,
                    path: result.path,
                    uploadTime: result.upload_time
                };

                // If the backend managed to generate a draft blueprint from
                // the document, immediately hydrate the Blueprint tab with it
                // so the user sees auto-filled sliders, pillars, and policies.
                if (result.blueprint) {
                    this.brand.blueprint = {
                        ...this.brand.blueprint,
                        ...result.blueprint
                    };

                    // Keep the onboarding product slider in sync when possible
                    if (typeof result.blueprint.productDefaultPct === 'number') {
                        this.settings.productDefaultPct = result.blueprint.productDefaultPct;
                    }

                // Update brand data
                this.brand.guidelineDoc = this.guidelineDoc;

                // Simulate processing
                setTimeout(() => {
                    this.guidelineDoc.status = 'parsed';
                    this.brand.guidelineDoc.status = 'parsed';
                }, 0);
                } else {
                    // Fallback: keep the existing "processing" behaviour
                    setTimeout(() => {
                        this.guidelineDoc.status = 'parsed';
                        this.brand.guidelineDoc.status = 'parsed';
                    }, 2000);
                }

            } catch (error) {
                console.error('Upload failed:', error);
                this.guidelineDoc.status = 'error';
                alert(`Upload failed: ${error.message}`);
            } finally {
                this.isUploading = false;
            }
        },

        /**
         * Save settings to backend
         */
        async saveSettings() {
            this.isSaving = true;

            try {
                await client.saveSettings(this.brand.id, this.settings);
                console.log('Settings saved successfully');
            } catch (error) {
                console.error('Failed to save settings:', error);
                alert(`Failed to save settings: ${error.message}`);
            } finally {
                this.isSaving = false;
            }
        },

        /**
         * Save blueprint to backend
         */
        async saveBlueprint() {
            this.isSaving = true;

            try {
                await client.saveBlueprint(this.brand.id, this.brand.blueprint);
                console.log('Blueprint saved successfully');
                this.brand.blueprint.status = 'saved';
            } catch (error) {
                console.error('Failed to save blueprint:', error);
                alert(`Failed to save blueprint: ${error.message}`);
            } finally {
                this.isSaving = false;
            }
        },

        /**
         * Generate brand blueprint with auto-save
         */
        async generateBrandBlueprint() {
            this.isGeneratingBlueprint = true;

            // Save current settings first
            await this.saveSettings();

            setTimeout(async () => {
                this.brand.blueprint.status = 'generated';

                // Auto-save the generated blueprint
                await this.saveBlueprint();

                this.isGeneratingBlueprint = false;
                this.activeTab = 'blueprint';
            }, 3000);
        },

        /**
         * Re-generate blueprint from uploaded document
         */
        async regenerateBlueprintFromDoc() {
            if (!this.brand.guidelineDoc || !this.brand.guidelineDoc.path) {
                alert('Please upload a guideline document first.');
                return;
            }
            
            this.isRegenerating = true;
            
            try {
                const response = await fetch(`${client.apiBase}/regenerate-blueprint/${this.brand.id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to regenerate blueprint');
                }
                
                const result = await response.json();
                
                // Update blueprint with regenerated data
                if (result.blueprint) {
                    this.brand.blueprint = {
                        ...this.brand.blueprint,
                        ...result.blueprint
                    };
                    
                    // Update product percentage in settings if changed
                    if (typeof result.blueprint.productDefaultPct === 'number') {
                        this.settings.productDefaultPct = result.blueprint.productDefaultPct;
                    }
                    
                    // Auto-save the regenerated blueprint
                    await this.saveBlueprint();
                    
                    console.log('Blueprint regenerated successfully from document');
                }
                
            } catch (error) {
                console.error('Regeneration error:', error);
                alert(`Failed to regenerate blueprint: ${error.message}`);
            } finally {
                this.isRegenerating = false;
            }
        },

        /**
         * Auto-save when settings change
         */
        async onSettingsChange() {
            // Debounce auto-save
            clearTimeout(this.saveTimeout);
            this.saveTimeout = setTimeout(() => {
                this.saveSettings();
            }, 1000);
        },

        /**
         * Auto-save when blueprint changes
         */
        async onBlueprintChange() {
            // Debounce auto-save
            clearTimeout(this.blueprintSaveTimeout);
            this.blueprintSaveTimeout = setTimeout(() => {
                this.saveBlueprint();
            }, 2000);
        },

        // Enhanced pillar management with auto-save
        async addPillar() {
            this.brand.blueprint.pillars.push({
                name: '',
                description: '',
                weight: 0
            });
            await this.onBlueprintChange();
        },

        async removePillar(index) {
            this.brand.blueprint.pillars.splice(index, 1);
            await this.onBlueprintChange();
        },

        // Enhanced phrase management with auto-save
        async addForbiddenPhrase() {
            if (this.newForbiddenPhrase.trim()) {
                this.brand.blueprint.policies.forbiddenPhrases.push(this.newForbiddenPhrase.trim());
                this.newForbiddenPhrase = '';
                await this.onBlueprintChange();
            }
        },

        async addBrandHashtag() {
            if (this.newBrandHashtag.trim()) {
                const hashtag = this.newBrandHashtag.startsWith('#') ? this.newBrandHashtag : '#' + this.newBrandHashtag;
                this.brand.blueprint.policies.brandHashtags.push(hashtag);
                this.newBrandHashtag = '';
                await this.onBlueprintChange();
            }
        },

        // ... rest of the original functions remain the same
        // (generatePlan, calculatePlanSummary, etc.)
    };
}

// Export for use in HTML
if (typeof window !== 'undefined') {
    window.BrandRegistrationClient = BrandRegistrationClient;
    window.enhancedBrandContentSystem = enhancedBrandContentSystem;
}