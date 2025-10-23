FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p templates

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. `.dockerignore`
```
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.env.*
.git/
.gitignore
*.md
venv/
env/
.vscode/
.idea/
*.log
```

### 3. `.gitignore` (si no existe)
```
__pycache__/
*.pyc
.env
.env.*
venv/
env/
*.log
.DS_Store
templates/*.docx
!templates/plantilla_ejemplo.docx