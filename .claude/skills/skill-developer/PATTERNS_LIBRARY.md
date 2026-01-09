# Common Patterns Library

Ready-to-use regex and glob patterns for skill triggers. Copy and customize for your skills.

---

## Intent Patterns (Regex)

### Feature/Endpoint Creation
```regex
(add|create|implement|build).*?(feature|endpoint|route|service|controller)
```

### Component Creation
```regex
(create|add|make|build).*?(component|UI|page|modal|dialog|form)
```

### Database Work
```regex
(add|create|modify|update).*?(user|table|column|field|schema|migration)
(database|prisma).*?(change|update|query)
```

### Error Handling
```regex
(fix|handle|catch|debug).*?(error|exception|bug)
(add|implement).*?(try|catch|error.*?handling)
```

### Explanation Requests
```regex
(how does|how do|explain|what is|describe|tell me about).*?
```

### Workflow Operations
```regex
(create|add|modify|update).*?(workflow|step|branch|condition)
(debug|troubleshoot|fix).*?workflow
```

### Testing
```regex
(write|create|add).*?(test|spec|unit.*?test)
```

---

## File Path Patterns (Glob)

### Python Source
```glob
src/**/*.py                 # All Python source files
lib/**/*.py                 # Library files
app/**/*.py                 # Application files
```

### C/C++ Source
```glob
src/**/*.cpp                # C++ source files
src/**/*.c                  # C source files
include/**/*.h              # C header files
include/**/*.hpp            # C++ header files
```

### CUDA Source
```glob
**/*.cu                     # CUDA source files
**/*.cuh                    # CUDA header files
kernels/**/*.cu             # CUDA kernels
```

### Database/Config
```glob
**/schema.sql               # SQL schema files
**/migrations/**/*.sql      # Migration files
**/*.yaml                   # YAML config files
**/*.json                   # JSON config files
```

### Test Exclusions
```glob
**/*_test.py                # Python tests (_test suffix)
**/test_*.py                # Python tests (test_ prefix)
**/*.test.cpp               # C++ tests
**/tests/**                 # Test directories
```

---

## Content Patterns (Regex)

### Python Database
```regex
import.*sqlalchemy              # SQLAlchemy imports
from.*database import           # Database imports
session\.(query|add|commit)     # Database session operations
```

### Python Imports
```regex
^import\s+\w+                   # Standard imports
^from\s+\w+\s+import            # From imports
__init__\.py                    # Package initialization
```

### Error Handling
```regex
try:                            # Try blocks
except\s+\w+:                   # Except blocks
raise\s+\w+Error                # Raise statements
```

### C/C++ Patterns
```regex
#include\s*<.*>                 # System includes
#include\s*".*"                 # Local includes
extern\s+"C"                    # C linkage
template\s*<                    # Template definitions
```

### CUDA Patterns
```regex
__global__\s+void               # CUDA kernels
__device__\s+                   # Device functions
cudaMalloc|cudaMemcpy           # CUDA API calls
```

---

**Usage Example:**

```json
{
  "my-skill": {
    "promptTriggers": {
      "intentPatterns": [
        "(create|add|build).*?(module|function|class)"
      ]
    },
    "fileTriggers": {
      "pathPatterns": [
        "src/**/*.py"
      ],
      "contentPatterns": [
        "^import\\s+\w+",
        "^from\\s+\w+\\s+import"
      ]
    }
  }
}
```

---

**Related Files:**
- [SKILL.md](SKILL.md) - Main skill guide
- [TRIGGER_TYPES.md](TRIGGER_TYPES.md) - Detailed trigger documentation
- [SKILL_RULES_REFERENCE.md](SKILL_RULES_REFERENCE.md) - Complete schema