# Site Multimodal Artifacts

The training script in `src/models/site_multimodal.py` writes the OCR + BERT + image-grade artifacts here.

Generated files:

- `site_multimodal/text_model/` for the fine-tuned BERT-style text classifier
- `site_multimodal/image_grade_model.joblib` for the image grading classifier
- `site_multimodal/fusion_model.joblib` for the final score combiner
- `site_multimodal/metadata.json` for thresholds and evaluation metadata