from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Initialize the analyzer and anonymizer engines globally for performance
# (so we only load the spaCy model once when the module/app loads)
try:
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
except Exception as e:
    print(f"⚠️ Failed to initialize Presidio engines: {e}")
    analyzer = None
    anonymizer = None

def mask_text(text: str) -> str:
    """
    Masks names and email addresses in the given text using Microsoft Presidio.
    Uses the globally initialized engines for speed.
    """
    if not analyzer or not anonymizer:
        return text
    try:
        results = analyzer.analyze(
            text=text,
            entities=["PERSON", "EMAIL_ADDRESS"],
            language='en'
        )
        anonymized_result = anonymizer.anonymize(
            text=text,
            analyzer_results=results
        )
        return anonymized_result.text
    except Exception:
        return text

def mask_text_with_mapping(text: str) -> tuple[str, dict[str, str]]:
    """
    Masks names and email addresses in the text with unique placeholders.
    Returns: (masked_text, pii_map) where pii_map maps placeholder -> original value.
    """
    if not analyzer or not anonymizer:
        return text, {}
    try:
        results = analyzer.analyze(
            text=text,
            entities=["PERSON", "EMAIL_ADDRESS"],
            language='en'
        )
        
        # Sort results from end to start to avoid shifting index offsets
        sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
        
        pii_map = {}
        masked_text = text
        person_count = 0
        email_count = 0
        
        for res in sorted_results:
            orig_val = text[res.start:res.end]
            if res.entity_type == "PERSON":
                placeholder = f"PERSON_PLACEHOLDER_{person_count}"
                person_count += 1
            elif res.entity_type == "EMAIL_ADDRESS":
                placeholder = f"EMAIL_PLACEHOLDER_{email_count}"
                email_count += 1
            else:
                continue
            
            pii_map[placeholder] = orig_val
            masked_text = masked_text[:res.start] + placeholder + masked_text[res.end:]
            
        return masked_text, pii_map
    except Exception as e:
        print(f"⚠️ Error during masking with mapping: {e}")
        return text, {}

if __name__ == "__main__":
    sample_text = "Please contact John Doe at john.doe@example.com regarding the new database structure."
    
    print("Original Text:")
    print(sample_text)
    print("-" * 50)
    
    masked_text_str = mask_text(sample_text)
    print("Masked Text (Legacy):")
    print(masked_text_str)
    print("-" * 50)

    masked_with_map, mapping = mask_text_with_mapping(sample_text)
    print("Masked Text with Placeholders:")
    print(masked_with_map)
    print("Mapping:")
    print(mapping)

