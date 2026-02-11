const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const XLSX = require('xlsx');

const app = express();
const PORT = process.env.PORT || 3000;

const upload = multer({ dest: path.join(__dirname, 'uploads') });

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const PROJECT_ROOT = path.join(__dirname, '..');
const PYTHON_DEFAULT = path.join(PROJECT_ROOT, 'venv', 'bin', 'python');
const PYTHON_EXECUTABLE = process.env.PYTHON_PATH || PYTHON_DEFAULT;

app.post('/api/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  try {
    const workbook = XLSX.readFile(req.file.path);
    const sheetName = workbook.SheetNames[0];
    const sheet = workbook.Sheets[sheetName];
    const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });

    const companies = [];
    for (let i = 1; i < rows.length; i += 1) {
      const row = rows[i];
      if (!row || !row[0]) continue;
      const name = String(row[0]).trim();
      if (name) companies.push(name);
    }

    if (companies.length === 0) {
      return res.status(400).json({ error: 'No company names found in the first column of the sheet' });
    }

    const tempDir = path.join(__dirname, 'temp');
    fs.mkdirSync(tempDir, { recursive: true });

    const timestamp = Date.now();
    const inputCsvPath = path.join(tempDir, `input_${timestamp}.csv`);
    const outputXlsxPath = path.join(tempDir, `output_${timestamp}.xlsx`);

    const csvLines = ['CompanyName', ...companies.map(name => `"${name.replace(/"/g, '""')}"`)];
    fs.writeFileSync(inputCsvPath, csvLines.join('\n'), 'utf8');

    const py = spawn(PYTHON_EXECUTABLE, ['main.py', '--input', inputCsvPath, '--output', outputXlsxPath], {
      cwd: PROJECT_ROOT,
    });

    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    py.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    py.on('close', (code) => {
      try {
        if (code !== 0) {
          console.error('Python script failed', { code, stdout, stderr });
          return res.status(500).json({
            error: 'Processing failed in Python pipeline',
            details: stderr || stdout,
          });
        }

        if (!fs.existsSync(outputXlsxPath)) {
          return res.status(500).json({ error: 'Output file not created by Python script' });
        }

        const resultWb = XLSX.readFile(outputXlsxPath);
        const resultSheet = resultWb.Sheets[resultWb.SheetNames[0]];
        const resultRows = XLSX.utils.sheet_to_json(resultSheet);

        const results = resultRows.map((row) => ({
          companyName: row.CompanyName || '',
          website: row.Website || '',
          businessDescription: row.BusinessDescription || '',
        }));

        // Keep the Excel file for download
        const downloadFileName = `results_${timestamp}.xlsx`;
        const downloadPath = path.join(tempDir, downloadFileName);
        fs.copyFileSync(outputXlsxPath, downloadPath);

        return res.json({ 
          results,
          downloadUrl: `/api/download/${downloadFileName}`
        });
      } finally {
        // Cleanup temp files (but keep the download file)
        try { fs.unlinkSync(req.file.path); } catch (e) {}
        try { fs.unlinkSync(inputCsvPath); } catch (e) {}
        try { fs.unlinkSync(outputXlsxPath); } catch (e) {}
      }
    });
  } catch (err) {
    console.error('Upload processing error', err);
    return res.status(500).json({ error: 'Failed to process uploaded file' });
  }
});

// Download endpoint for Excel files
app.get('/api/download/:filename', (req, res) => {
  const tempDir = path.join(__dirname, 'temp');
  const filePath = path.join(tempDir, req.params.filename);
  
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'File not found' });
  }
  
  res.download(filePath, req.params.filename, (err) => {
    if (!err) {
      // Delete file after download
      setTimeout(() => {
        try { fs.unlinkSync(filePath); } catch (e) {}
      }, 5000);
    }
  });
});

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});
