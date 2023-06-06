# Shadow Clone API

### A cheat detection system for student assignments. Built as a Web API to compare repository content with a set of repositories.

---

## Getting Started

- Edit the app configurations in `shadow_clone_api.shadow_clone_api.py`.
  - Pick either `config.ProdConfig` or `config.DevConfig`.
  - Edit these two in `config.py` file.
  - Provide environment variables in `.env` file as shown in `.env.sample`.
- Use the command `flask run` to start the server.

---

## Request Samples

```js
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
```

---

## Goals

- [x] Read Parameters from Request
- [ ] Handle errors and Exceptions
- [ ] Validate all requests
- [x] Checking for limit rate
- [x] Can search for existing reports
- [x] Can Download all reports
- [x] Can remove all existing reports
- [ ] Send process status
- [x] Stream Terminal Output
- [x] Separate download handler
- [x] Add detection logic
- [x] Fetch Cohorts data
- [x] Add Cohorts and Courses
- [x] Edit Cohorts and Courses
- [x] Delete Cohorts and Courses
- [ ] Refine model interactions
- [x] Generate Daily Access Token
- [x] Generate Temporary Access Token
- [x] WebSocket Authentication
- [x] Manage CORS
- [x] Automatically provide user emails with Access Tokens
  - [x] Setup mailing endpoint
  - [x] Trigger mailing API on schedule
- [x] Create Temporary Front-End template
  - [x] Allow Authentication Through Template
  - [x] Allow Sending Data Through Template
  - [x] Allow Streaming Data Through Template
  - [x] Provide Proper Feedback Through Template
  - [x] Minimal Sensitive Parameters Leak
- [x] Prepare for deployment
  - [x] Add Docker files
  - [x] Add Heroku files
  - [x] Add Production Server
- [ ] Implement Account Authentication
  - [ ] Email Server
  - [ ] Account model
  - [ ] Account creation
  - [ ] Account Password reset
  - [ ] Session Token
- [ ] Structured/Free Query mode

---

## Troubleshooting

- Check Github Token Expiry
- Check JWT (Expiry/Match Secret)
- Check Emails Auth Trigger Engine
- Check Emails Auth Trigger JWT
- Check Email Account Tokens and Credentials
- Check OAuth info and redirect URIs
- Check Websocket Secure state
- Check Websocket (URL)s
