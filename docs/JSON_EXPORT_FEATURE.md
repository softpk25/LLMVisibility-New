# JSON Export Feature Documentation

## Overview

The brand blueprint page now includes JSON export functionality, allowing users to download their brand blueprint and content packages as JSON files for backup, sharing, or integration with other tools.

## Features Implemented

### 1. Save JSON Button (Brand Blueprint Tab)

**Location:** Brand Blueprint tab header, next to "Approve Blueprint" button

**Button Label:** "Save JSON" (previously "Save Draft")

**Functionality:**
- Downloads the complete brand blueprint as a formatted JSON file
- Includes all brand configuration data
- Generates filename with brand name and date

**JSON Structure:**
```json
{
  "brandId": "brand-001",
  "brandName": "TechBrand",
  "version": "1.0.0",
  "status": "draft",
  "exportedAt": "2026-02-09T12:00:00.000Z",
  "voice": {
    "formality": 50,
    "humor": 30,
    "warmth": 60,
    "emojiPolicy": "light"
  },
  "contentPillars": [
    {
      "name": "Innovation",
      "description": "Latest tech trends",
      "weight": 30
    }
  ],
  "policies": {
    "forbiddenPhrases": ["buy now", "limited time"],
    "maxHashtags": 5,
    "brandHashtags": ["#TechBrand", "#Innovation"]
  },
  "productDefaultPct": 30,
  "guidelineDocument": {
    "name": "brand_guidelines.pdf",
    "status": "processed"
  }
}
```

**Filename Format:** `{BrandName}_blueprint_{YYYY-MM-DD}.json`

**Example:** `TechBrand_blueprint_2026-02-09.json`

### 2. Export Package Button (Calendar Tab)

**Location:** Calendar/Export tab header

**Button Label:** "Export Package (CSV/JSON)"

**Functionality:**
- Exports all approved posts as both JSON and CSV files
- Downloads two files simultaneously
- Includes complete post data with scheduling information

**JSON Structure:**
```json
{
  "campaign": {
    "id": "campaign-001",
    "objective": "Increase brand awareness",
    "duration": 7,
    "startDate": "2026-02-09",
    "language": "en"
  },
  "brand": {
    "id": "brand-001",
    "name": "TechBrand"
  },
  "exportedAt": "2026-02-09T12:00:00.000Z",
  "totalPosts": 15,
  "posts": [
    {
      "postId": 1,
      "day": 1,
      "pillar": "Innovation",
      "topic": "AI Breakthroughs",
      "format": "Reel",
      "productIncluded": true,
      "caption": "Exciting developments in AI...",
      "hooks": "Did you know AI can...",
      "hashtags": "#Innovation #AI #TechBrand",
      "version": "1.0",
      "scheduledDate": "2026-02-10",
      "scheduledTime": "09:00"
    }
  ]
}
```

**CSV Structure:**
```csv
Day,Pillar,Topic,Format,Product Included,Caption,Hashtags,Scheduled Date,Scheduled Time
1,Innovation,AI Breakthroughs,Reel,Yes,"Exciting developments in AI...",#Innovation #AI #TechBrand,2026-02-10,09:00
```

**Filename Format:** 
- JSON: `{BrandName}_content_package_{YYYY-MM-DD}.json`
- CSV: `{BrandName}_content_package_{YYYY-MM-DD}.csv`

**Example:** 
- `TechBrand_content_package_2026-02-09.json`
- `TechBrand_content_package_2026-02-09.csv`

## User Flow

### Exporting Brand Blueprint

1. Navigate to the Brand Blueprint tab
2. Configure your brand settings (voice, pillars, policies)
3. Click the "💾 Save JSON" button
4. JSON file downloads automatically to your browser's download folder
5. Success message confirms the download

### Exporting Content Package

1. Navigate to the Calendar/Export tab
2. Ensure you have approved posts (green checkmarks)
3. Click "Export Package (CSV/JSON)" button
4. Both JSON and CSV files download automatically
5. Success message shows the number of posts exported

## Use Cases

### Brand Blueprint JSON

**Backup and Version Control:**
- Save different versions of your brand blueprint
- Track changes over time
- Restore previous configurations

**Team Collaboration:**
- Share brand guidelines with team members
- Import into other tools or platforms
- Maintain consistency across teams

**Integration:**
- Import into content management systems
- Feed into AI content generation tools
- Integrate with marketing automation platforms

### Content Package Export

**Content Scheduling:**
- Import CSV into social media scheduling tools (Buffer, Hootsuite, etc.)
- Bulk upload to Facebook Business Suite
- Schedule posts in third-party platforms

**Content Review:**
- Share with stakeholders for approval
- Review content calendar offline
- Archive completed campaigns

**Analytics and Reporting:**
- Import into spreadsheet tools for analysis
- Track content performance by pillar
- Generate reports on content mix

## Technical Implementation

### Frontend (JavaScript)

**downloadBlueprintJSON():**
- Collects all brand blueprint data
- Formats as JSON with 2-space indentation
- Creates Blob object with MIME type `application/json`
- Generates download link and triggers download
- Cleans up resources after download

**exportPackage():**
- Filters approved posts only
- Creates both JSON and CSV formats
- Handles CSV escaping for special characters
- Downloads both files sequentially
- Shows summary of exported content

### Browser Compatibility

Works in all modern browsers:
- Chrome/Edge (Chromium)
- Firefox
- Safari
- Opera

**Requirements:**
- JavaScript enabled
- Blob API support (all modern browsers)
- Download attribute support

## File Size Considerations

**Brand Blueprint JSON:**
- Typical size: 2-10 KB
- Maximum expected: ~50 KB (with extensive data)

**Content Package:**
- JSON: 10-100 KB (depending on post count)
- CSV: 5-50 KB (more compact than JSON)
- 100 posts ≈ 50 KB JSON, 25 KB CSV

## Security and Privacy

**Client-Side Processing:**
- All JSON generation happens in the browser
- No data sent to external servers during export
- Files are created locally and downloaded directly

**Data Included:**
- Brand configuration (non-sensitive)
- Content drafts and captions
- Scheduling information
- No API keys or access tokens

**Recommendations:**
- Store exported files securely
- Don't share files containing proprietary content publicly
- Use version control for blueprint files

## Troubleshooting

### Download Doesn't Start

**Possible Causes:**
- Browser blocking downloads
- Pop-up blocker enabled
- Insufficient permissions

**Solutions:**
- Check browser download settings
- Allow downloads from the site
- Try a different browser

### File Opens Instead of Downloads

**Cause:** Browser configured to open JSON files

**Solution:**
- Right-click the button and select "Save Link As"
- Change browser settings to download JSON files
- Use "Save As" from the browser menu after opening

### Empty or Incomplete JSON

**Cause:** Data not loaded or form not filled

**Solution:**
- Ensure all required fields are filled
- Wait for page to fully load
- Refresh page and try again

### CSV Special Characters Issue

**Cause:** Excel or other tools misinterpreting CSV

**Solution:**
- Open CSV in text editor first to verify
- Use UTF-8 encoding when importing
- Use proper CSV import settings in Excel

## Future Enhancements

Potential improvements:
- Import JSON to restore blueprint
- Batch export multiple campaigns
- Export to additional formats (XLSX, PDF)
- Cloud storage integration (Google Drive, Dropbox)
- Automatic backup scheduling
- Version comparison tool
- Export templates for different platforms

## API Integration

While the current implementation is client-side only, the JSON format is designed to be compatible with future API endpoints:

**Potential Endpoints:**
```
POST /api/brand/blueprint/import
POST /api/campaign/import
GET /api/brand/blueprint/export
GET /api/campaign/export
```

## Support

For issues or questions:
- Check browser console for errors
- Verify JavaScript is enabled
- Try incognito/private browsing mode
- Contact support with error details
