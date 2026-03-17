---
description: Trace a PyTorch function's cross-language binding chain (Python -> C++ -> CUDA)
argument-hint: <function-name> [focus]
---

## Name
odh-ai-helpers:torchtalk-trace

## Synopsis
```
/torchtalk:trace <function-name>
/torchtalk:trace <function-name> full
/torchtalk:trace <function-name> dispatch
/torchtalk:trace <function-name> yaml
```

## Description
The `torchtalk:trace` command traces a PyTorch function's complete binding chain from Python through C++ to CUDA implementations. It uses the TorchTalk MCP server to look up operator definitions in `native_functions.yaml`, find pybind11 and TORCH_LIBRARY bindings, and map dispatch keys to backend implementations.

After gathering the raw binding data, the command analyzes the results to explain:
- How the Python API connects to the native implementation
- Which dispatch keys route to which backends (CPU, CUDA, MPS, etc.)
- Where each layer is implemented with exact file:line references
- The autograd integration and backward pass formula (if applicable)
- Architectural context about why the dispatch is structured this way

This command requires the TorchTalk MCP server to be running. Run `mcp__torchtalk__get_status` to verify availability.

## Prerequisites
- TorchTalk MCP server must be running and registered with Claude Code
- Run `/torchtalk:setup` if not yet installed

## Implementation
1. **Verify MCP server**: Call `mcp__torchtalk__get_status` to confirm the TorchTalk server is running and has indexed data available
2. **Trace binding chain**: Call `mcp__torchtalk__trace` with the function name and optional focus parameter to retrieve the full binding chain
3. **Get internal dependencies**: Call `mcp__torchtalk__calls` with the function name to understand what the function invokes internally
4. **Analyze dispatch architecture**: Examine the dispatch keys, backend routing, and structured binding patterns returned by the trace
5. **Synthesize explanation**: Combine the trace data, call graph, and dispatch information into a coherent explanation that covers:
   - The Python entry point and how it connects to native code
   - The `native_functions.yaml` definition and its dispatch configuration
   - Each backend implementation with file:line references
   - The autograd formula (from `derivatives.yaml`) if applicable
   - Architectural observations about the operator's design
6. **Provide file references**: Format all implementation locations as `file:line` references so the developer can navigate directly to the source

## Return Value
- **Claude agent text**: A structured analysis of the function's binding chain, organized by layer (Python -> YAML definition -> C++ dispatch -> backend implementations), with file:line references and architectural commentary

## Examples

1. **Trace a common operator**:
   ```
   /torchtalk:trace matmul
   ```
   Output: Full binding chain from `torch.matmul` through `at::native::matmul` to `LinearAlgebra.cpp`, including CPU and CUDA dispatch paths.

2. **Focus on dispatch mapping only**:
   ```
   /torchtalk:trace conv2d dispatch
   ```
   Output: Which backends handle `conv2d` and where each kernel is registered.

3. **Focus on YAML definition**:
   ```
   /torchtalk:trace softmax yaml
   ```
   Output: The `native_functions.yaml` entry for softmax, including its function schema, dispatch keys, and derivative formula.

4. **Full deep trace**:
   ```
   /torchtalk:trace add full
   ```
   Output: Complete trace from Python API through every layer including structured kernel registrations, autograd formula, and all backend implementations.

## Arguments
- `<function-name>`: The PyTorch function name to trace (e.g., `matmul`, `conv2d`, `softmax`, `add`). Can be a short name or fully qualified (e.g., `at::native::matmul`).
- `[focus]`: Optional focus parameter. One of:
  - `full` (default): Complete binding chain across all layers
  - `dispatch`: Only dispatch key to backend mapping
  - `yaml`: Only the `native_functions.yaml` definition

## See Also
- `/torchtalk:setup` - Install and configure TorchTalk
- TorchTalk Analyzer skill - Full MCP tools reference including impact analysis, call graph, and test infrastructure
