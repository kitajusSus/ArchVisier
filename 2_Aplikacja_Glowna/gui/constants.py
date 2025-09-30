DOC_TYPE_LABELS = {
    "KP": "Korespondencja Przychodzaca (KP)",
    "KW": "Korespondencja Wychodzaca (KW)",
    "SA": "Sad Arbitrazowy (SA)",
}

LABEL_TO_CODE = {label: code for code, label in DOC_TYPE_LABELS.items()}

TYPE_PATTERNS = {
    "KP": "KP/{num}/{year}",
    "KW": "KW/{num}/{year}",
    "SA": "SA{num}_{year}",
}
