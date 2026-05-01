

import os
import logging

MOCK_API = True  

# ServiceNow
SNOW_INSTANCE = os.getenv("SNOW_INSTANCE", "dev12345")
SNOW_USERNAME  = os.getenv("SNOW_USERNAME",  "admin")
SNOW_PASSWORD  = os.getenv("SNOW_PASSWORD",  "password")

# Jira
JIRA_DOMAIN     = os.getenv("JIRA_DOMAIN",      "yourcompany")
JIRA_EMAIL      = os.getenv("JIRA_EMAIL",        "you@example.com")
JIRA_API_TOKEN  = os.getenv("JIRA_API_TOKEN",    "your_jira_token")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "IT")

# Azure Boards
AZURE_ORG     = os.getenv("AZURE_ORG",     "your-org")
AZURE_PROJECT = os.getenv("AZURE_PROJECT", "IncidentTracker")
AZURE_PAT     = os.getenv("AZURE_PAT",     "your_azure_pat")

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = None
logging.basicConfig(
    level=logging.INFO
)