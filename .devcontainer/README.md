# Dev Containers

This follows the standard dev container workflow. See [Development Containers](https://containers.dev/).

## Prerequisites

1. **Git Configuration**  
    Ensure you have a global Git configuration. If not, run the following commands:

    ```bash
    git config --global user.name "Your Name"
    git config --global user.email "your-email@example.com"
    ```

2. **Claude Configuration**  
    This dev container assumes your certs for Claude are managed by Vertex AI via GCP. 
    Please make sure you have set up the files on your host; they will be mounted automatically. If you have used claude on your current host before, proceed to the next step.

    Verify certs are present on host.

    ```bash
    ls /home/.config/gcloud
    ```
    Should return something like this:
    ```text
    access_tokens.db  application_default_credentials.json  configurations  default_configs.db  legacy_credentials
    active_config     config_sentinel                       credentials.db  gce                 logs
    ```

    If it does not, there are two possibilities:

    i. **You have never used Claude Code**
    - Please refer to your organization’s setup guide for Claude Code.

    ii. **You have used Claude Code before, but not on this node**
    - Transfer your certificates to the new host using:
        ```text
        ai-helpers/scripts/scp_cred.sh
        ```
        
3. **Dev Container Json Configuration** 

    The devcontainer.json file in this repository was written for a generic project and region. Please update the values with your respective organization's values. 

    CLOUD_ML_REGION - Your GCP region (e.g., us-east5)
    ANTHROPIC_VERTEX_PROJECT_ID - Your GCP project ID

## Using the Container

You can now proceed with the standard steps for opening your project in the container. All necessary installations and volumes will be taken care of. Enjoy!