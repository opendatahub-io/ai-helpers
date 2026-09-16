# Konflux sandbox dummy project

This minimal project exists to verify GitHub onboarding and pull-request and
push PipelineRuns in a non-production Konflux tenant.

The `Containerfile` accepts optional `BASE_IMAGE`, `PROJECT_OWNER`, and
`BUILD_MESSAGE` build arguments. Supply values through the generated pipeline
configuration if customization is needed.
