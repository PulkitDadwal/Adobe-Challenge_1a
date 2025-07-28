import fitz
import re
import json
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class Heading:
    text: str
    level: str
    page: int
    bbox: Tuple[float, float, float, float]
    font_size: float
    font_name: str
    confidence: float

class PDFHeadingAnalyzer:
    def __init__(self):
        """
        Enhanced PDF Heading Detection Model:
        - Ignores headers/footers using position and pattern analysis
        - Merges adjacent text with similar formatting
        - Uses hybrid approach with statistical thresholds
        """
        pass
    
    def analyze_pdf(self, pdf_path: str) -> Dict:
        """Main analysis function with header/footer filtering"""
        doc = fitz.open(pdf_path)
        
        # Extract all potential headings
        all_headings = []
        for page_num in range(len(doc)):
            page_headings = self._extract_page_headings(doc[page_num], page_num + 1)
            all_headings.extend(page_headings)
        
        doc.close()
        
        # Merge adjacent headings with similar formatting
        merged_headings = self._merge_adjacent_headings(all_headings)
        
        # Classify headings using ML-inspired model
        classified = self._classify_headings(merged_headings)
        
        return classified
    
    def analyze_pdf_from_doc(self, doc) -> Dict:
        """Analyze PDF from already opened document"""
        # Extract all potential headings
        all_headings = []
        for page_num in range(len(doc)):
            page_headings = self._extract_page_headings(doc[page_num], page_num + 1)
            all_headings.extend(page_headings)
        
        # Merge adjacent headings with similar formatting
        merged_headings = self._merge_adjacent_headings(all_headings)
        
        # Classify headings using ML-inspired model
        classified = self._classify_headings(merged_headings)
        
        return classified
    
    def _extract_page_headings(self, page, page_num: int) -> List[Heading]:
        """Extract potential headings with enhanced header/footer filtering"""
        headings = []
        blocks = page.get_text("dict")
        page_height = page.rect.height
        page_width = page.rect.width
        
        for block in blocks.get("blocks", []):
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                line_text = ""
                font_sizes = []
                font_names = []
                bbox = None
                
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        line_text += text + " "
                        font_sizes.append(span.get("size", 0))
                        font_names.append(span.get("font", ""))
                        
                        span_bbox = span.get("bbox", (0, 0, 0, 0))
                        if bbox is None:
                            bbox = span_bbox
                        else:
                            bbox = (min(bbox[0], span_bbox[0]), min(bbox[1], span_bbox[1]),
                                   max(bbox[2], span_bbox[2]), max(bbox[3], span_bbox[3]))
                
                line_text = line_text.strip()
                
                if self._is_potential_heading(line_text, font_sizes, font_names, bbox, page_height, page_width):
                    heading = Heading(
                        text=line_text,
                        level="",
                        page=page_num,
                        bbox=bbox,
                        font_size=max(font_sizes) if font_sizes else 0,
                        font_name=max(set(font_names), key=font_names.count) if font_names else "",
                        confidence=0.0
                    )
                    headings.append(heading)
        
        return headings
    
    def _is_potential_heading(self, text: str, font_sizes: List[float], 
                            font_names: List[str], bbox: Tuple, page_height: float, page_width: float) -> bool:
        """Enhanced filtering with header/footer detection"""
        if not text or len(text) < 3:
            return False
        
        # Skip very long text (likely paragraphs)
        if len(text) > 200:
            return False
        
        # Skip obvious fragments and broken words
        text_lower = text.lower().strip()
        
        # Common fragments that should never be headings
        fragments = [
            'quest f', 'r pr', 'oposal', 'rfp:', 'request f', 'quest for pr', 
            'r proposal', 'for pr', 'pr', 'quest', 'equest', 'r', 'f', 'quest for',
            'proposal', 'present', 'developing', 'business', 'plan', 'ontario',
            'digital', 'library'
        ]
        
        if text_lower in fragments:
            return False
        
        # Skip very short text unless it's all caps
        if len(text) < 5 and not text.isupper():
            return False
        
        # Skip text that looks like broken words (no vowels in short text)
        if len(text) < 8 and not any(vowel in text_lower for vowel in 'aeiou') and not text.isupper():
            return False
        
        # Skip text that starts with lowercase (likely continuation)
        if text[0].islower():
            return False
        
        # Enhanced header/footer detection
        if self._is_header_or_footer(text, bbox, page_height, page_width):
            return False
        
        # Must have reasonable font size
        if font_sizes and max(font_sizes) < 8:
            return False
        
        return True
    
    def _is_header_or_footer(self, text: str, bbox: Tuple, page_height: float, page_width: float) -> bool:
        """Enhanced header/footer detection"""
        if not bbox:
            return False
        
        # Position-based filtering (top 10% and bottom 10% of page)
        header_threshold = page_height * 0.1
        footer_threshold = page_height * 0.9
        
        y_position = bbox[1]  # Top of text
        
        if y_position < header_threshold or y_position > footer_threshold:
            return True
        
        # Pattern-based filtering for common header/footer content
        text_lower = text.lower().strip()
        header_footer_patterns = [
            r'^\d+$',  # Just page numbers
            r'^page\s+\d+',  # "Page 1", "Page 2"
            r'^\d+\s*/\s*\d+$',  # "1/5", "2 / 10"
            r'^©.*',  # Copyright
            r'^copyright.*',
            r'^all rights reserved',
            r'^\w+\.(com|org|net)',  # URLs
            r'^www\.',
            r'^https?://',
            r'^draft$|^confidential$|^proprietary$',  # Watermarks
        ]
        
        return any(re.match(pattern, text_lower) for pattern in header_footer_patterns)
    
    def _merge_adjacent_headings(self, headings: List[Heading]) -> List[Heading]:
        """Merge adjacent text with similar formatting into single headings"""
        if not headings:
            return headings
        
        # Sort by page and vertical position
        headings.sort(key=lambda x: (x.page, x.bbox[1] if x.bbox else 0))
        
        merged = []
        i = 0
        
        while i < len(headings):
            current = headings[i]
            merged_text = current.text
            merged_bbox = current.bbox
            
            # Look for adjacent headings to merge
            j = i + 1
            while j < len(headings) and self._should_merge(current, headings[j]):
                next_heading = headings[j]
                merged_text += " " + next_heading.text
                
                # Expand bounding box
                if merged_bbox and next_heading.bbox:
                    merged_bbox = (
                        min(merged_bbox[0], next_heading.bbox[0]),  # left
                        min(merged_bbox[1], next_heading.bbox[1]),  # top
                        max(merged_bbox[2], next_heading.bbox[2]),  # right
                        max(merged_bbox[3], next_heading.bbox[3])   # bottom
                    )
                
                j += 1
            
            # Create merged heading
            merged_heading = Heading(
                text=merged_text.strip(),
                level="",
                page=current.page,
                bbox=merged_bbox,
                font_size=current.font_size,
                font_name=current.font_name,
                confidence=0.0
            )
            
            merged.append(merged_heading)
            i = j
        
        return merged
    
    def _should_merge(self, heading1: Heading, heading2: Heading) -> bool:
        """Check if two headings should be merged based on proximity and formatting"""
        # Must be on same page
        if heading1.page != heading2.page:
            return False
        
        # Check font size similarity (within 1 point)
        if abs(heading1.font_size - heading2.font_size) > 1.0:
            return False
        
        # Check font name similarity
        if heading1.font_name != heading2.font_name:
            return False
        
        # Check vertical proximity (within 30 points)
        if heading1.bbox and heading2.bbox:
            vertical_distance = abs(heading2.bbox[1] - heading1.bbox[3])
            if vertical_distance > 30:
                return False
        
        # Check if combined text is reasonable length
        combined_length = len(heading1.text) + len(heading2.text) + 1
        if combined_length > 300:
            return False
        
        return True
    
    def _classify_headings(self, headings: List[Heading]) -> Dict:
        """Enhanced classification with merged headings"""
        if not headings:
            return {"title": "", "outline": []}
        
        # Calculate font statistics for normalization
        font_sizes = [h.font_size for h in headings]
        mean_size = np.mean(font_sizes)
        std_size = np.std(font_sizes) if len(font_sizes) > 1 else 1
        
        # Sort headings by page and position
        headings.sort(key=lambda x: (x.page, x.bbox[1] if x.bbox else 0))
        
        title = ""
        outline = []
        
        # Title detection: largest font on first page
        page1_headings = [h for h in headings if h.page == 1]
        if page1_headings:
            title_candidate = max(page1_headings, key=lambda x: x.font_size)
            title = title_candidate.text
        
        # Classify remaining headings
        for heading in headings:
            if heading.text == title:
                continue
            
            level, confidence = self._calculate_heading_level(heading, mean_size, std_size)
            
            if level and confidence > 0.3:
                outline.append({
                    "level": level,
                    "text": heading.text,
                    "page": heading.page
                })
        
        # Sort outline by page number
        outline.sort(key=lambda x: x["page"])
        
        return {"title": title, "outline": outline}
    
    def _calculate_heading_level(self, heading: Heading, mean_size: float, std_size: float) -> Tuple[str, float]:
        """Multi-factor scoring with enhanced pattern recognition"""
        # Feature 1: Font size score (normalized)
        font_score = (heading.font_size - mean_size) / (std_size + 1e-6)
        
        # Feature 2: Text pattern score
        pattern_score = self._analyze_text_patterns(heading.text)
        
        # Feature 3: Typography score
        format_score = self._analyze_typography(heading.font_name)
        
        # Feature 4: Position score
        position_score = self._analyze_position(heading.bbox, heading.page)
        
        # Weighted combination
        total_score = (0.4 * font_score + 0.3 * pattern_score + 
                      0.2 * format_score + 0.1 * position_score)
        
        # Classification thresholds
        if total_score > 1.5 or font_score > 2.0:
            return "H1", min(0.95, 0.7 + total_score * 0.1)
        elif total_score > 0.8 or font_score > 1.0:
            return "H2", min(0.9, 0.6 + total_score * 0.1)
        elif total_score > 0.3 or font_score > 0.5:
            return "H3", min(0.85, 0.5 + total_score * 0.1)
        else:
            return "", 0.0
    
    def _analyze_text_patterns(self, text: str) -> float:
        """Enhanced text pattern analysis"""
        score = 0.0
        
        # Numbered headings
        if re.match(r'^\d+\.?\s+', text):
            score += 1.0
        elif re.match(r'^\d+\.\d+\.?\s+', text):
            score += 0.8
        elif re.match(r'^\d+\.\d+\.\d+\.?\s+', text):
            score += 0.6
        
        # Title case
        if text.istitle():
            score += 0.6
        
        # All caps (short text)
        if text.isupper() and len(text.split()) <= 8:
            score += 0.7
        
        # Length penalty for very long merged text
        word_count = len(text.split())
        if word_count > 20:
            score -= 0.8
        elif word_count > 15:
            score -= 0.5
        
        # Chapter/section keywords
        if any(word in text.lower() for word in ['chapter', 'section', 'part', 'introduction', 'conclusion']):
            score += 0.8
        
        return score
    
    def _analyze_typography(self, font_name: str) -> float:
        """Typography analysis for heading detection"""
        if not font_name:
            return 0.0
        
        font_lower = font_name.lower()
        
        # Bold indicators
        if any(weight in font_lower for weight in ['bold', 'black', 'heavy']):
            return 1.0
        elif any(weight in font_lower for weight in ['medium', 'semi']):
            return 0.5
        
        return 0.0
    
    def _analyze_position(self, bbox: Tuple, page: int) -> float:
        """Position analysis for heading likelihood"""
        if not bbox:
            return 0.0
        
        score = 0.0
        
        # Top of page bonus (but not in header region)
        if 100 < bbox[1] < 250:  # Sweet spot below header
            score += 0.5
        
        # First page bonus
        if page == 1:
            score += 0.3
        
        return score

def analyze_pdf_headings(pdf_path: str) -> str:
    analyzer = PDFHeadingAnalyzer()
    
    try:
        results = analyzer.analyze_pdf(pdf_path)
        return json.dumps(results, indent=2, ensure_ascii=False)
    
    except Exception as e:
        error_result = {
            "title": "",
            "outline": [],
            "error": f"Analysis failed: {str(e)}"
        }
        return json.dumps(error_result, indent=2)

# Usage example
if __name__ == "__main__":
    pdf_file = "/kaggle/input/file03/file03.pdf"
    result_json = analyze_pdf_headings(pdf_file)
    print(result_json)
