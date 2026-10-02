from typing import List

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Splits text into chunks of `chunk_size` characters with `overlap` characters.
    This is a basic chunking algorithm for MVP.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        # If not at the end of the text, try to find a newline or space to break at
        if end < text_length:
            # Look for last newline within the overlap area
            break_point = text.rfind('\n', start + chunk_size - overlap, end)
            if break_point == -1:
                # Fallback to space
                break_point = text.rfind(' ', start + chunk_size - overlap, end)
            
            if break_point != -1:
                end = break_point + 1 # Include the space/newline in current chunk
                
        chunks.append(text[start:end].strip())
        
        # Next chunk starts after overlapping part
        start = end - overlap if end < text_length else text_length
        
    # Remove any empty chunks
    return [c for c in chunks if c]
