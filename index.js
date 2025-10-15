import express from "express";
import multer from "multer";
import fs from "fs";
import path from "path";
import libre from "libreoffice-convert";
import axios from "axios";

const app = express();
const port = process.env.PORT || 3000;

// Ensure uploads directory exists (important for Docker)
if (!fs.existsSync("uploads")) fs.mkdirSync("uploads");

// Multer setup for file uploads
const upload = multer({ dest: "uploads/" });

// Middlewares
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Wrap libre.convert into a Promise
const convertLibre = (inputFile, ext) =>
  new Promise((resolve, reject) => {
    libre.convert(inputFile, ext, undefined, (err, done) => {
      if (err) return reject(err);
      resolve(done);
    });
  });

// 🚀 Universal file conversion endpoint
app.post("/convert", upload.single("file"), async (req, res) => {
  try {
    const { format, url } = req.body;

    // Validate parameters
    if (!format) {
      return res.status(400).json({
        title: "Missing format",
        code: 400,
        message: "You must specify a target format (e.g., pdf, docx, txt, odt).",
      });
    }

    if (!req.file && !url) {
      return res.status(400).json({
        title: "Missing file or URL",
        code: 400,
        message: "You must upload a file or provide a URL to convert.",
      });
    }

    let inputFile;
    let filename = "converted";
    let inputExt;

    if (req.file) {
      // Read the uploaded file
      inputFile = fs.readFileSync(req.file.path);
      filename = path.parse(req.file.originalname).name;
      inputExt = path.extname(req.file.originalname).slice(1);
      fs.unlinkSync(req.file.path); // Clean up after reading
    } else if (url) {
      // Fetch file from URL
      try {
        const response = await axios.get(url, { responseType: "arraybuffer" });
        inputFile = Buffer.from(response.data);
        filename = path.basename(url, path.extname(url));
        inputExt = path.extname(url).slice(1);
      } catch {
        return res.status(400).json({
          title: "Invalid URL",
          code: 400,
          message: "Could not fetch file from URL.",
        });
      }
    }

    const targetExt = `.${format.toLowerCase()}`;

    // Run LibreOffice conversion
    const converted = await convertLibre(inputFile, targetExt);

    res.setHeader(
      "Content-Disposition",
      `attachment; filename="${filename}${targetExt}"`
    );
    res.setHeader("Content-Type", "application/octet-stream");
    res.send(converted);
  } catch (err) {
    console.error("❌ Conversion error:", err);
    res.status(500).json({
      title: "Conversion Error",
      code: 500,
      message: err.message || "An unexpected error occurred during conversion.",
    });
  }
});

// 🩺 Health check
app.get("/health", (req, res) => {
  res.json({ status: "OK", uptime: process.uptime() });
});

// Root route
app.get("/", (req, res) => {
  res.json({
    service: "Endless Document Conversion API",
    version: "1.0.0",
    uptime: process.uptime(),
  });
});

app.listen(port, () => {
  console.log(`✅ Document converter running at http://localhost:${port}`);
});
