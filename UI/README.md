# Docling Document Parser - Frontend UI

A beautiful dark-themed web interface for the Docling Document Parser API with amethyst haze styling.

## Features

### Upload & Parse Documents
- Upload PDF, DOCX, HTML, Markdown, and image files
- Configure parsing modes (standard, fast, high_quality, ocr)
- Extract images and tables
- Generate AI descriptions for images using Docling (SmolVLM), Gemini, or OpenAI
- Real-time progress tracking

### Job Management
- View all parsing jobs with status badges
- Filter jobs by status (pending, processing, completed, failed)
- Real-time status updates with automatic polling
- Job details modal with progress tracking

### Results Viewer
- View complete document metadata and statistics
- Browse content in multiple formats:
  - **Markdown Tab**: Full document as markdown
  - **Text Items Tab**: Structured text with filters (by page, by label)
  - **Tables Tab**: View tables as structured data or CSV
  - **Images Tab**: Gallery view with captions and AI descriptions
- Export results as Markdown or JSON

### API Information
- View supported file types and formats
- Check parsing modes and configuration limits
- API health monitoring

## Getting Started

### Prerequisites
1. The Docling API must be running at `http://localhost:8000`
2. A modern web browser (Chrome, Firefox, Edge, Safari)

### Running the UI

#### Option 1: Simple Python Server
```bash
cd UI
python -m http.server 8080
```
Then open `http://localhost:8080` in your browser.

#### Option 2: Node.js Server
```bash
cd UI
npx http-server -p 8080
```
Then open `http://localhost:8080` in your browser.

#### Option 3: Direct File Access
Simply open `index.html` in your browser. Note: Some features may not work due to CORS restrictions.

### Configuration

To change the API URL, edit the following line in both `app.js` and `results.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## File Structure

```
UI/
├── index.html          # Main page - upload & job management
├── results.html        # Results viewer page
├── styles.css          # Dark amethyst theme styles
├── app.js             # Main functionality (upload, jobs, API)
├── results.js         # Results viewing functionality
└── README.md          # This file
```

## Usage Guide

### Uploading a Document

1. Open `index.html` in your browser
2. Select a document file
3. Choose parsing mode:
   - **Standard**: Balanced quality and speed
   - **Fast**: Quick processing
   - **High Quality**: Best accuracy
   - **OCR**: For scanned documents and images
4. Configure options:
   - Extract images
   - Extract tables
   - Image quality scale (1.0 - 4.0)
5. Optionally enable AI image descriptions:
   - Choose provider (Docling, Gemini, OpenAI)
   - Add custom description prompt
6. Click "Upload & Parse Document"
7. Monitor progress in the jobs section

### Viewing Results

1. Once a job is completed, click "View Results"
2. Browse different content types using tabs:
   - **Markdown**: Full document text
   - **Texts**: Filter and browse text items
   - **Tables**: View structured table data
   - **Images**: Gallery with descriptions
3. Export results as Markdown or JSON

### Managing Jobs

- **Refresh**: Click the refresh button to update job list
- **Filter**: Use the status filter to show specific job types
- **Status**: Click "Status" to see detailed job information
- **Auto-polling**: Active jobs are automatically monitored

## Theme

The UI uses a dark amethyst haze theme with:
- Deep purple and violet backgrounds
- Lavender and magenta accents
- Smooth transitions and hover effects
- Responsive design for mobile and desktop

## Color Palette

- Primary: `#0d0221` (Deep dark purple)
- Accent: `#9d4edd` (Amethyst)
- Highlights: `#c77dff` (Lavender)
- Text: `#e8dff5` (Light purple-white)

## API Endpoints Used

- `POST /api/v1/parse/document` - Upload document
- `GET /api/v1/parse/jobs/{job_id}` - Get job status
- `GET /api/v1/jobs` - List all jobs
- `GET /api/v1/parse/results/{job_id}` - Get results
- `GET /api/v1/parse/results/{job_id}/texts` - Get filtered texts
- `GET /api/v1/parse/results/{job_id}/tables` - Get tables
- `GET /api/v1/parse/results/{job_id}/images` - Get images
- `GET /api/v1/parse/results/{job_id}/export/markdown` - Export markdown
- `GET /api/v1/parse/results/{job_id}/export/json` - Export JSON
- `GET /api/v1/info` - API information
- `GET /health` - Health check

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### API Connection Failed
- Ensure the API is running at `http://localhost:8000`
- Check the API health at `http://localhost:8000/health`
- Verify CORS is configured correctly in the API

### Jobs Not Updating
- Click the refresh button manually
- Check browser console for errors
- Verify the API is responding

### Images Not Displaying
- Ensure images were extracted during parsing
- Check that base64 image URIs are valid
- Verify browser supports the image format

## Development

To modify the UI:

1. **Styles**: Edit `styles.css` for theme and layout changes
2. **Upload Logic**: Edit `app.js` for upload and job management
3. **Results Logic**: Edit `results.js` for results viewing
4. **HTML Structure**: Edit `index.html` or `results.html` for layout

## License

Part of the Docling Document Parser project.
