# Creating & Switching Workspaces

Learn how to create new team workspaces and switch between different workspaces.

## Creating Team Workspaces

To create a new team workspace for collaboration:

### Step 1: Access Workspace Creation

1. Navigate to the **Workspaces** section in the sidebar
2. Click **Create New Workspace**
3. The workspace creation dialog will appear


### Step 2: Configure Your Workspace

1. **Workspace Name**: Enter a descriptive name for your team workspace
3. **Create**: Click the create button

### Notes
- Workspace names must be unique across the platform
- You automatically become the administrator of workspaces you create

### What Happens Next
- A new team workspace is created with you as the administrator
- A unique API key is generated for the workspace
- You can immediately start inviting team members
- You can begin creating experiments within the workspace

## Switching Between Workspaces

You can easily switch between any workspaces you have access to.

### Using the Workspace Switcher

1. Click the **Workspace Switcher** in the sidebar header
2. A dropdown will show all available workspaces
3. Select the workspace you want to switch to
4. The interface will reload with that workspace's content


### What Changes When You Switch

- **Authentication Token**: Updates to reflect the new workspace
- **Experiments Shown**: Only experiments from the selected workspace
- **API Configuration**: Workspace-specific API keys and settings
- **User Permissions**: Your role in the new workspace takes effect

## Managing Multiple Workspaces

### Workspace Organization Tips

**Clear Naming Convention**:
```
Personal Workspace (your default)
ProjectName-Production
ProjectName-Development
TeamName-Experiments
```

**Environment Separation**:
```
Production Workspace    (live experiments)
Staging Workspace      (pre-production testing)
Development Workspace  (development and testing)
```

### Keeping Track of Workspaces

- **Bookmark Important Workspaces**: Note which workspaces you use most frequently
- **Document Purpose**: Keep track of what each workspace is used for
- **Regular Review**: Periodically review and clean up unused workspaces


## Next Steps

<div class="grid cards" markdown>

-   :octicons-gear-24:{ .lg .middle } __Managing Workspaces__

    ---

    Learn how to manage settings, API keys, and team members

    [:octicons-arrow-right-24: Managing Workspaces](./managing.md)

-   :octicons-tools-24:{ .lg .middle } __Create Your First Experiment__

    ---

    Ready to create experiments in your workspace?

    [:octicons-arrow-right-24: Setup Experiment](../first-experiment/index.md)

</div>
