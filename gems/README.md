# Gemini Gems Collection

This directory contains a curated collection of Gemini Gems that complement the AI Helpers marketplace, providing specialized AI assistants for various development and technical tasks.

## What are Gemini Gems?

Gemini Gems are custom AI assistants that you can create and configure within Google's Gemini platform. Each Gem can be tailored with specific instructions, knowledge bases, and capabilities to excel at particular tasks like code review, documentation writing, or technical analysis.

Unlike Claude Code plugins that extend functionality through commands, Gemini Gems provide specialized conversational AI assistants that can be shared and reused across different projects and workflows.

## How to Create and Share Gemini Gems

### Creating a Gem

1. **Access Gemini**: Go to [Gemini](https://gemini.google.com/) and sign in with your Google account
2. **Create New Gem**: Look for the option to create a new Gem in the interface
3. **Configure Your Gem**:
   - Give it a descriptive name
   - Write detailed instructions about its purpose and behavior
   - Add any specific knowledge or guidelines it should follow
   - Test it thoroughly with example prompts
4. **Save and Share**: Once satisfied, save your Gem and get its shareable link

### Sharing Guidelines

When sharing Gemini Gems in this collection:

- **Title**: Use a clear, descriptive name that explains the Gem's purpose
- **Description**: Provide a concise explanation of what the Gem does and its key capabilities
- **Link**: Include the public sharing link to the Gem

### Adding to This Collection

To add your Gem to this collection:

1. Edit the `gems.yaml` file in this directory
2. Add your gem entry following this format:
   ```yaml
   - title: "Your Gem Title"
     description: "Clear description of what your gem does and its capabilities."
     link: "https://gemini.google.com/gem/your-gem-id"
   ```
3. Run `make update` to update the generated content.
4. Submit a merge request with your addition

> [!IMPORTANT]
> Make sure the Gem was [shared](https://support.google.com/gemini/answer/16504957).

