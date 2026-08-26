---
name: torchtalk-analyzer
description: Analyze PyTorch internals across Python, C++, and CUDA layers using the TorchTalk MCP server. Use when asked about how PyTorch operators work internally, where functions are implemented, what would break if code is modified, or finding tests for PyTorch operators.
allowed-tools: Bash Read Grep Glob
---

# TorchTalk Analyzer

This skill enables cross-language analysis of PyTorch internals by leveraging the TorchTalk MCP server. It traces binding chains from Python through C++ to CUDA, analyzes dispatch mechanisms, maps call graphs, and locates test infrastructure.

## When to Use

- When asked how a PyTorch operator works internally (e.g., "How does torch.add dispatch to CUDA?")
- When investigating where a function is implemented across CPU/CUDA/MPS backends
- When assessing what would break if a C++ function is modified (impact analysis)
- When tracing how torch.nn modules connect to native ATen operators
- When finding existing tests for a PyTorch operator or function
- When exploring PyTorch's dispatch architecture or autograd integration

## Prerequisites

- TorchTalk MCP server must be running and registered with Claude Code
- PyTorch source code must be available locally
- Run `/torchtalk:setup` if TorchTalk is not yet installed

Verify availability:
```text
mcp__torchtalk__get_status
```

If the status tool returns data, all tools below are ready.

## Instructions

### Step 1 - Verify MCP Server

Before using any tools, confirm the TorchTalk server is running:

```text
mcp__torchtalk__get_status
```

Check that:
- Bindings are loaded (should show thousands of bindings)
- Native functions are parsed
- C++ call graph status is "Ready" (required for impact/calls/called_by)
- Python modules are loaded (required for trace_module/list_modules)

If the server is not available, direct the user to run `/torchtalk:setup`.

---

### Step 2 - Identify the Analysis Type

Match the user's question to the appropriate tool:

| Question Pattern | Tool | Example |
|---|---|---|
| "How does X work?" / "Trace X" | `mcp__torchtalk__trace` | `trace("softmax", "full")` |
| "Find functions matching X" | `mcp__torchtalk__search` | `search("conv", "CUDA")` |
| "Where are the CUDA kernels for X?" | `mcp__torchtalk__cuda_kernels` | `cuda_kernels("softmax")` |
| "What does X call?" | `mcp__torchtalk__calls` | `calls("at::native::add")` |
| "What calls X?" | `mcp__torchtalk__called_by` | `called_by("at::native::add")` |
| "What breaks if I change X?" | `mcp__torchtalk__impact` | `impact("at::native::add", 3)` |
| "How does nn.Linear work?" | `mcp__torchtalk__trace_module` | `trace_module("Linear")` |
| "List all nn modules" | `mcp__torchtalk__list_modules` | `list_modules("nn")` |
| "Find tests for X" | `mcp__torchtalk__find_similar_tests` | `find_similar_tests("softmax")` |
| "What test utilities exist?" | `mcp__torchtalk__list_test_utils` | `list_test_utils("all")` |
| "What tests are in file X?" | `mcp__torchtalk__test_file_info` | `test_file_info("test_torch")` |

---

### Step 3 - Execute and Synthesize

For simple lookups, a single tool call suffices. For deeper questions, combine multiple tools:

**"How does torch.softmax work end-to-end?"**
1. `mcp__torchtalk__trace("softmax", "full")` - Get the binding chain
2. `mcp__torchtalk__cuda_kernels("softmax")` - Find GPU kernels
3. `mcp__torchtalk__calls("at::native::softmax")` - See internal dependencies

**"What breaks if I modify at::native::add?"**
1. `mcp__torchtalk__impact("at::native::add", 3)` - Transitive callers
2. `mcp__torchtalk__find_similar_tests("add")` - Affected tests

**"How does nn.Linear connect to native code?"**
1. `mcp__torchtalk__trace_module("Linear")` - Module definition
2. `mcp__torchtalk__trace("linear", "full")` - Native operator chain

---

### Step 4 - Present Results

Format results with:
- Clear layer separation (Python -> YAML -> C++ -> CUDA)
- `file:line` references for every implementation location
- Architectural context explaining *why* the dispatch is structured this way
- Suggestions for further exploration if the user wants to go deeper

## MCP Tools Reference

### ATen Operators
| Tool | Parameters | Description |
|---|---|---|
| `mcp__torchtalk__trace` | `function_name`, `focus?` | Trace Python to C++ binding chain. Focus: "full", "yaml", "dispatch" |
| `mcp__torchtalk__search` | `query`, `backend?`, `limit?` | Find bindings by name with optional backend filter |
| `mcp__torchtalk__cuda_kernels` | `function_name?` | Find GPU kernel launches with file:line |

### C++ Call Graph
| Tool | Parameters | Description |
|---|---|---|
| `mcp__torchtalk__impact` | `function_name`, `depth?` | Transitive callers + Python entry points (depth 1-5) |
| `mcp__torchtalk__calls` | `function_name` | Functions this function invokes (outbound) |
| `mcp__torchtalk__called_by` | `function_name` | Functions that invoke this (inbound) |

### Python Modules
| Tool | Parameters | Description |
|---|---|---|
| `mcp__torchtalk__trace_module` | `module_name` | Trace torch.nn.Linear, torch.optim.Adam, etc. |
| `mcp__torchtalk__list_modules` | `category?` | List modules: "nn" (default), "optim", "all", or search query |

### Test Infrastructure
| Tool | Parameters | Description |
|---|---|---|
| `mcp__torchtalk__find_similar_tests` | `query`, `limit?` | Find tests for an operator or concept |
| `mcp__torchtalk__list_test_utils` | `category?` | List test utilities: "all" (default), "fixtures", "assertions", "decorators" |
| `mcp__torchtalk__test_file_info` | `file_path` | Details about a specific test file |

## Error Handling

- **MCP server not running**: Direct user to `/torchtalk:setup`
- **"C++ call graph not available"**: PyTorch needs to be built once (`python setup.py develop`) to generate `compile_commands.json`
- **"Function not found"**: Use `mcp__torchtalk__search` with partial names, or check spelling
- **"Test infrastructure not loaded"**: Verify PyTorch source path is correct with `torchtalk status`
