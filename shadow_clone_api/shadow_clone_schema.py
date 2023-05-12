"""This module contains JSON requests schemas"""

clone_schema = {
    "type": "object",
    "properties": {
        "MAX_THREADS": {"type": "number"},
        "SIMILARITY_THRESHOLD": {"type": "number"},
        "TESTS": {"type": "boolean"},
        "CHEATER_REPORT": {"type": "boolean"},
        "QUICK_MODE": {"type": "boolean"},
        "LEGACY": {"type": "boolean"},
        "EXCEL": {"type": "boolean"},
        "course": {"type": "string"},
        "owners": {"type": "array"},
        "repository": {"type": "string"},
        "cohort": {"type": "string"},
    },
    "required": [
        "MAX_THREADS",
        "SIMILARITY_THRESHOLD",
        "TESTS",
        "CHEATER_REPORT",
        "QUICK_MODE",
        "LEGACY",
        "EXCEL",
        "course",
        "owners",
        "repository",
        "cohort",
    ],
}

add_cohort_schema = {
    "type": "object",
    "properties": {
        "cohort": {"type": "string", "maxLength": 64},
        "course": {"type": "string", "maxLength": 12},
        "students": {"type": "array"},
    },
    "required": ["cohort", "course", "students"],
}

manage_cohort_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "cohort": {"type": "string", "maxLength": 64},
        "course": {"type": "string", "maxLength": 12},
        "students": {"type": "array", "items": {"type": "object"}},
    },
    "required": ["id", "cohort", "course", "students"],
}

manage_student_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "number"},
        "cohort": {"type": "string", "maxLength": 64},
        "students": {"type": "array", "items": {"type": "object"}},
    },
    "required": ["id", "cohort", "students"],
}
