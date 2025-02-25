from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import os
import subprocess
import pick

# Acquire a credential object.
credential = DefaultAzureCredential()

# Retrieve subscription ID from azure cli
subscription_id = subprocess.check_output('az account show --query id -o tsv', shell=True).decode().strip()
print("Using default Azure Subscription. Change the Subscription with 'az account set -s <subscriptionId>'")
print("Subscription ID: ", subscription_id)

# Obtain the management object for resources.
resource_client = ResourceManagementClient(credential, subscription_id)

# Retrieve the list of resource groups with Adventure Day Tag present
group_list = resource_client.resource_groups.list(filter="tagName eq 'azd-env-name'")

title = "Select the Azure Adventure Day Agent to connect to: "
options = [group.tags.get("azd-env-name") for group in list(group_list)]
selected_group = pick.pick(options, title)[0]

os.system(f"azd up -e {selected_group} --no-prompt")
print(f"Connected to Azure Adventure Day Agent: {selected_group}")
print("Setting up local environment...")
os.system("source <(azd env get-values | grep AZURE_ENV_NAME)")
print("Local environment setup complete.")
print("You can now proceed to deploy a phase.")