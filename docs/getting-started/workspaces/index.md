# Workspaces Overview

Workspaces are organizational containers that help you group and manage your experiments. All experiments in ExE are created within a workspace, which provides isolation, access control, and team collaboration.

## What are Workspaces?

A workspace is a logical boundary that contains:

- **Experiments**: All your A/B tests, multi-armed bandits, and contextual bandits
- **API Configuration**: Unique API keys for secure access
- **User Access**: Team members with different permission levels (for team workspaces)
- **Organization**: Group experiments by project, team, or environment


## Key Features

<div class="grid cards" markdown>

-   :octicons-organization-24:{ .lg .middle } __Experiment Organization__

    ---

    Group experiments by project, team, or environment

-   :octicons-key-24:{ .lg .middle } __API Key Management__

    ---

    Secure, workspace-specific API keys with rotation support

-   :octicons-people-24:{ .lg .middle } __Team Collaboration__

    ---

    Role-based permissions for team workspaces

-   :octicons-shield-24:{ .lg .middle } __Isolation & Security__

    ---

    Complete separation between different workspaces

</div>

## How Workspaces Work

### Experiment Isolation
- All experiments belong to a specific workspace
- Experiment IDs are unique within each workspace
- Complete data separation between workspaces

### API Integration
- Each workspace has its own unique API key
- All API calls are scoped to the workspace
- Secure authentication for each workspace

### Access Control
- Personal workspaces: Single user access only
- Team workspaces: Multiple users with role-based permissions
- Complete isolation between different workspaces

## Next Steps

<div class="grid cards" markdown>

-   :octicons-people-24:{ .lg .middle } __Personal vs Team Workspaces__

    ---

    Learn about the different types of workspaces

    [:octicons-arrow-right-24: Personal vs Team](./personal-vs-team.md)

-   :octicons-plus-24:{ .lg .middle } __Creating & Switching__

    ---

    Learn how to create and switch between workspaces

    [:octicons-arrow-right-24: Creating & Switching](./creating-switching.md)

-   :octicons-gear-24:{ .lg .middle } __Managing Workspaces__

    ---

    Manage settings, API keys, and team members

    [:octicons-arrow-right-24: Managing Workspaces](./managing.md)

</div>
