# Managing Workspaces

Learn how to manage workspace settings, API keys, and team members.

## Accessing Workspace Settings

Access workspace settings by clicking **Manage Workspace** from the workspace overview or settings menu.


## Workspace Information
- **Workspace Name**: Update the display name
- **Creation Date**: When the workspace was created
- **Administrator**: Who manages the workspace


## API Key Management

### Viewing Your API Key

For security, only the first few characters of your API key are displayed in the interface. The full key is only shown when rotating an existing key.

### API Key Information
- **Key Prefix**: First few characters (e.g., `exe_abc...`)
- **Created Date**: When the key was generated
- **Last Rotated**: Most recent rotation date
- **Rotated By**: User who performed the last rotation

### Rotating API Keys

Rotate your workspace API key periodically for security:

1. Go to workspace settings (Manage)
2. Navigate to the **API** configuration tab
3. Click **Rotate API Key**
4. Confirm the action in the dialog
5. **Important**: Copy the new key immediately
6. Update any applications using the old key


!!! warning "Important"
    Rotating a key immediately invalidates the old key. Make sure to update all applications before rotating.

### Key Rotation History

Track when API keys were rotated:

- **Date & Time**: When each rotation occurred
- **Rotated By**: Which user performed the rotation
- **Key Prefix**: First characters of each rotated key

## Team Management (Team Workspaces Only)

!!! note "Personal Workspaces"
    Personal workspaces do not support team member invitations. Only team workspaces allow collaboration.

### Adding Team Members

For team workspaces, invite users to collaborate:

1. Go to workspace settings
2. Click the **Users** tab
3. Click **Invite User**
4. Enter their email address
5. Select a role (Admin or Read-only)
6. Click **Send Invitation**


### Invitation Process

The invited user will receive an email with instructions to:

- Create an account to join the workspace (If they don't have one). Once they will create account, they will add to that workspace.
- Accept the workspace invitation if they have account
- Access the workspace

### Managing Existing Users

**View Team Members**:

- See all current workspace members
- View their roles and permissions
- Check when they joined

**Remove Users**:

- Click **Remove** next to a user's name
- Confirm the removal
- User immediately loses access to the workspace


## Workspace Maintenance

### Regular Tasks

**Monthly**:

- Review team member access
- Check API key rotation dates
- Clean up unused experiments

**Quarterly**:

- Rotate API keys for production workspaces
- Review workspace organization

### Data Management

**Experiment Cleanup**:

- Organize experiments with clear naming

**Access Review**:

- Remove inactive team members
- Ensure principle of least privilege


## Next Steps

<div class="grid cards" markdown>

-   :octicons-tools-24:{ .lg .middle } __Create Experiments__

    ---

    Ready to start creating experiments?

    [:octicons-arrow-right-24: Setup Experiment](../first-experiment/index.md)

</div>
