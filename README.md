# PDF2Text Converter

AI-powered PDF text extraction with support for large files, built with Docker, FastAPI, and modern web technologies.

<img width="1298" height="722" alt="immagine" src="https://github.com/user-attachments/assets/39f7c41f-bb34-4b94-8a9e-f098b1aac58a" />

## Features

- **AI-Powered Extraction**: Uses Tesseract OCR and PyMuPDF for accurate text extraction
- **Text Filtering**: Remove repetitive headers, footers, and copyright notices
- **Text Normalization**: Automatic ligature replacement and Unicode normalization
- **GPU Support**: Optional GPU acceleration for faster processing
- **Large File Support**: Intelligent chunking for processing very large PDF files
- **Streaming Mode**: Real-time feedback during processing
- **Multi-language OCR**: Support for English, Italian, French, German, Spanish
- **Web Interface**: Modern, responsive UI for easy file upload and processing
- **REST API**: Full-featured API for programmatic access
- **Docker-based**: Easy deployment with Docker Compose
- **Modular Configuration**: Separate CPU and GPU configurations
- **CI/CD Ready**: GitHub Actions workflow for automated testing and deployment

## Architecture

```
pdf2text-converter/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── services/       # PDF processing services
│   │   └── utils/          # Chunking utilities
│   ├── Dockerfile          # CPU Docker image
│   └── Dockerfile.gpu      # GPU Docker image
├── frontend/               # Web interface
│   ├── index.html
│   └── static/
│       ├── css/
│       └── js/
├── docker-compose.yml      # Base configuration
├── docker-compose.gpu.yml  # GPU configuration
└── Makefile               # Management commands
```

## Requirements

### CPU Mode (Default)
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB free disk space

### GPU Mode (Optional)
- NVIDIA GPU with CUDA support
- NVIDIA Docker runtime
- CUDA 12.1+
- 8GB VRAM minimum

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd pdf2text-converter

# Create environment file
make install

# Edit .env if needed
nano .env
```

### 2. Start Services

**CPU Mode (Default):**
```bash
make build
make up
```

**GPU Mode:**
```bash
make build-gpu
make up-gpu
```

### 3. Access the Application

- **Web Interface**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **API Endpoint**: http://localhost:8000/api
- **Health Check**: http://localhost:8000/health

## Makefile Commands

Run `make help` to see all available commands:

### Basic Commands
- `make install` - Create .env file from template
- `make build` - Build Docker images (CPU mode)
- `make build-gpu` - Build Docker images (GPU mode)
- `make up` - Start services (CPU mode)
- `make up-gpu` - Start services (GPU mode)
- `make down` - Stop services
- `make restart` - Restart services

### Development
- `make dev` - Start in development mode with live logs
- `make logs` - View all service logs
- `make logs-backend` - View backend logs only
- `make shell` - Open shell in backend container
- `make status` - Show service status

### Testing
- `make test` - Test API with uploads/test.pdf
- `make test-all` - Run comprehensive test suite
- `make health` - Check backend health
- `make upload-test` - Upload test file

### Maintenance
- `make clean` - Stop services and remove volumes
- `make clean-all` - Remove everything including images
- `make rebuild` - Rebuild and restart (CPU)
- `make rebuild-gpu` - Rebuild and restart (GPU)

## Configuration

Edit `.env` file to customize:

```env
# Backend Configuration
BACKEND_PORT=8000          # Backend API port
WORKERS=4                  # Number of worker processes

# Frontend Configuration
FRONTEND_PORT=80          # Frontend web interface port

# GPU Configuration
USE_GPU=false             # Enable GPU support

# Upload Configuration
MAX_FILE_SIZE_MB=500      # Maximum file size
CHUNK_SIZE_MB=10          # Chunk size for large files

# Model Configuration
EXTRACTION_METHOD=tesseract  # Extraction method
```

## API Usage

### Extract Text (Standard)

```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "file=@document.pdf" \
  -F "use_ocr=true" \
  -F "chunk_processing=true" \
  -F "language=eng"
```

### Extract Text (Streaming)

```bash
curl -X POST "http://localhost:8000/api/extract-stream" \
  -F "file=@document.pdf" \
  -F "use_ocr=true" \
  -F "language=eng"
```

### Check API Status

```bash
curl http://localhost:8000/api/status
```

## Web Interface Usage

1. **Open Browser**: Navigate to http://localhost
2. **Upload PDF**: Drag and drop or click to browse
3. **Configure Options**:
   - Enable/disable OCR
   - Choose processing mode
   - Select language
4. **Process**: Click "Process PDF"
5. **View Results**: See extracted text with metadata
6. **Export**: Copy to clipboard or download as TXT

## Features in Detail

### Chunking for Large Files

The system automatically chunks large PDF files for efficient processing:

- Files larger than `CHUNK_SIZE_MB` are processed in chunks
- Each chunk is processed independently
- Progress is reported for each chunk
- Results are combined at the end

### OCR Support

Tesseract OCR is used for image-based PDFs:

- Automatic detection of image-based content
- Multi-language support (English, Italian, French, German, Spanish)
- Configurable OCR settings
- High-quality text extraction from scans

### Streaming Mode

Real-time processing feedback:

- Page-by-page processing
- Live progress updates
- Suitable for very large files
- Lower memory footprint

### GPU Acceleration

When GPU mode is enabled:

- Faster processing for image-heavy PDFs
- CUDA-accelerated operations
- Automatic GPU detection
- Fallback to CPU if GPU unavailable

## Troubleshooting

### Services won't start

```bash
# Check logs
make logs

# Rebuild images
make rebuild
```

### GPU not detected

```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Verify docker-compose GPU config
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml config
```

### Out of memory errors

- Reduce `CHUNK_SIZE_MB` in .env
- Reduce `WORKERS` count
- Increase Docker memory limits

### OCR quality issues

- Install additional language packs
- Adjust image preprocessing
- Use higher resolution scans

## Performance Tips

1. **CPU Mode**:
   - Adjust `WORKERS` based on CPU cores
   - Use chunk processing for files > 50MB
   - Enable OCR only when needed

2. **GPU Mode**:
   - Reduce `WORKERS` to 1-2 (GPU bound)
   - Increase batch size for better GPU utilization
   - Monitor VRAM usage

3. **Network**:
   - Use streaming mode for remote clients
   - Enable compression for large responses
   - Implement client-side caching

## Development

### Project Structure

- `backend/app/main.py` - FastAPI application
- `backend/app/api/routes.py` - API endpoints
- `backend/app/services/pdf_processor.py` - PDF processing logic
- `backend/app/utils/chunking.py` - Chunking utilities
- `frontend/static/js/app.js` - Frontend JavaScript
- `frontend/static/css/style.css` - Styles

### Adding New Features

1. Modify backend code in `backend/app/`
2. Update frontend in `frontend/static/`
3. Rebuild: `make rebuild`
4. Test: `make test`

### Running Tests

```bash
# Start services
make up

# Run API tests
make test

# Check health
make health
```

## CI/CD with GitHub Actions

The project includes automated testing and deployment workflows.

### Automated Tests

The GitHub Actions workflow (`.github/workflows/deploy-test.yml`) automatically:

1. **Builds** Docker images for CPU mode
2. **Starts** services in a clean environment
3. **Tests** all API endpoints:
   - Health checks
   - PDF extraction with/without filtering
   - Multi-language support
   - OCR toggle
   - Chunk processing
   - Error handling
4. **Benchmarks** extraction performance
5. **Generates** test reports

### Running Tests

**Locally:**
```bash
# Quick test with test.pdf
make test

# Comprehensive test suite
make test-all

# Or run directly
./tests/run-tests.sh
```

**GitHub Actions:**
- Automatically runs on push to main/master/develop branches
- Runs on pull requests
- Can be triggered manually via workflow_dispatch

### Test File

Place a `test.pdf` in the `uploads/` directory for testing:
- Used by automated tests
- Should be a representative PDF document
- Committed to repository (excluded from .gitignore)

## Security Considerations

- File size limits enforced
- File type validation
- Temporary file cleanup
- No persistent storage of uploads
- CORS configured for local development

## License

MIT License - feel free to use for any purpose.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions:

- Check the troubleshooting section
- Review logs: `make logs`
- Check API docs: http://localhost:8000/docs
- Open an issue on GitHub

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [Docker](https://www.docker.com/) - Containerization
- [Nginx](https://nginx.org/) - Web server
