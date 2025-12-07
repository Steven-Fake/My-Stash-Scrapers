def jaccard_similarity(str1: str, str2: str) -> float:
    """Calculate Jaccard similarity between two strings."""
    set1 = set(str1)
    set2 = set(str2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    if not union:
        return 0.0
    return len(intersection) / len(union)