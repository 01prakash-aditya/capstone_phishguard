#!/usr/bin/env python3
"""
PhishGuard++ Multi-Modal Trainer
Trains the complete phishing detection pipeline:
1. Color Grading CNN on screenshots (visual patterns)
2. BERT text classifier on OCR/HTML text
3. Fusion model combining both modalities
4. Gemini integration for low-confidence escalation
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.site_multimodal import train_site_multimodal_model
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Train PhishGuard++ multi-modal phishing detector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full training with default settings
  python train_multimodal.py --train
  
  # Quick training on subset (for testing)
  python train_multimodal.py --train --epochs 2 --max-samples 1000
  
  # Run with GPU acceleration
  CUDA_VISIBLE_DEVICES=0 python train_multimodal.py --train --epochs 5
        """
    )
    
    parser.add_argument(
        "--train",
        action="store_true",
        help="Train all models (Color CNN, BERT, Fusion)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs (default: 5)"
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Optional cap for dataset size (useful for testing)"
    )
    
    args = parser.parse_args()
    
    if args.train:
        logger.info("=" * 80)
        logger.info("Starting Multi-Modal Training Pipeline")
        logger.info("=" * 80)
        logger.info(f"Config:")
        logger.info(f"  - Epochs: {args.epochs}")
        logger.info(f"  - Max Samples: {args.max_samples or 'Unlimited'}")
        logger.info("=" * 80)
        
        metadata = train_site_multimodal_model(
            epochs=args.epochs,
            max_samples=args.max_samples
        )
        
        logger.info("=" * 80)
        logger.info("[OK] Training Complete!")
        logger.info("=" * 80)
        logger.info(f"Models saved to: {metadata.get('artifact_dir')}")
        logger.info(f"Test AUC: {metadata.get('test_auc', 0):.4f}")
        logger.info(f"Test F1:  {metadata.get('test_f1', 0):.4f}")
        
    else:
        from src.models.site_multimodal import site_detector
        import json
        logger.info("Displaying current model metadata:")
        print(json.dumps(site_detector.metadata, indent=2))

if __name__ == "__main__":
    main()
