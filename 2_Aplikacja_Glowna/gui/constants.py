DOC_TYPE_LABELS = {
    "KP": "Korespondencja Przychodząca (KP)",
    "KW": "Korespondencja Wychodząca (KW)",
    "SA": "Sąd Arbitrażowy (SA)",
}

LABEL_TO_CODE = {label: code for code, label in DOC_TYPE_LABELS.items()}

TYPE_PATTERNS = {
    "KP": "KP/{num}/{year}",
    "KW": "KW/{num}/{year}",
    "SA": "SA{num}_{year}",
}
