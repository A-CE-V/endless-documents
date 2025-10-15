import express from "express";
import multer from "multer";
import fs from "fs";
import path from "path";
import libre from "libreoffice-convert";
import axios from "axios";

const app = express();
const port = process.env.PORT || 3000;

// Ensure uploads directory exists
if (!fs.existsSync("uploads")) fs.mkdirSync("uploads");

// Multer setup
const upload = multer({ dest: "uploads/" });

// Middlewares
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Wrap libre.convert into a Promise and explicitly set soffice path
// Wrap libre.convert into a Promise
// Wrap libre.convert into a Promise
const convertLibre = (inputFile, ext) =>
  new Promise((resolve, reject) => {
    // Using the 3-argument signature: (inputFile, ext, callback)
    libre.convert(inputFile, ext, (err, done) => {
      if (err) return reject(err);
      resolve(done);
    });
  });


// Universal file conversion endpoint
app.post("/convert", upload.single("file"), async (req, res) => {
  try {
    const { format, url } = req.body;

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

    if (req.file) {
      inputFile = fs.readFileSync(req.file.path);
      filename = path.parse(req.file.originalname).name;
      fs.unlinkSync(req.file.path);
    } else if (url) {
      try {
        const response = await axios.get(url, { responseType: "arraybuffer" });
        inputFile = Buffer.from(response.data);
        filename = path.basename(url, path.extname(url));
      } catch {
        return res.status(400).json({
          title: "Invalid URL",
          code: 400,
          message: "Could not fetch file from URL.",
        });
      }
    }

    const targetExt = `.${format.toLowerCase()}`;
    const converted = await convertLibre(inputFile, targetExt);

    res.setHeader("Content-Disposition", `attachment; filename="${filename}${targetExt}"`);
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

// Health check
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
