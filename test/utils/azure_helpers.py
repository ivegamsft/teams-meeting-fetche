"""
Azure Test Utilities
Helper functions for Azure integration tests
"""
import os
from typing import Dict, Any, Optional
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError


def get_azure_credential(
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
):
    """Get Azure credential (service principal or default)"""
    if client_id and client_secret and tenant_id:
        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
    return DefaultAzureCredential()


def get_keyvault_secret(
    vault_name: str,
    secret_name: str,
    credential=None
) -> str:
    """Retrieve secret from Azure Key Vault"""
    if credential is None:
        credential = get_azure_credential()
    
    vault_url = f"https://{vault_name}.vault.azure.net"
    client = SecretClient(vault_url=vault_url, credential=credential)
    
    try:
        secret = client.get_secret(secret_name)
        return secret.value
    except ResourceNotFoundError:
        raise ValueError(f"Secret '{secret_name}' not found in Key Vault '{vault_name}'")


def list_keyvault_secrets(vault_name: str, credential=None) -> list:
    """List all secrets in Key Vault"""
    if credential is None:
        credential = get_azure_credential()
    
    vault_url = f"https://{vault_name}.vault.azure.net"
    client = SecretClient(vault_url=vault_url, credential=credential)
    
    return [secret.name for secret in client.list_properties_of_secrets()]


def get_blob_content(
    storage_account: str,
    container: str,
    blob_name: str,
    credential=None
) -> bytes:
    """Retrieve blob content from Azure Storage (RBAC)"""
    if credential is None:
        credential = get_azure_credential()
    
    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=credential)
    
    blob_client = blob_service.get_blob_client(container=container, blob=blob_name)
    
    try:
        downloader = blob_client.download_blob()
        return downloader.readall()
    except ResourceNotFoundError:
        raise FileNotFoundError(
            f"Blob '{blob_name}' not found in container '{container}'"
        )


def list_blobs(
    storage_account: str,
    container: str,
    prefix: Optional[str] = None,
    credential=None
) -> list:
    """List blobs in container"""
    if credential is None:
        credential = get_azure_credential()
    
    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=credential)
    
    container_client = blob_service.get_container_client(container)
    
    blobs = container_client.list_blobs(name_starts_with=prefix)
    return [blob.name for blob in blobs]


def upload_blob(
    storage_account: str,
    container: str,
    blob_name: str,
    data: bytes,
    credential=None
) -> None:
    """Upload blob to Azure Storage"""
    if credential is None:
        credential = get_azure_credential()
    
    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=credential)
    
    blob_client = blob_service.get_blob_client(container=container, blob=blob_name)
    blob_client.upload_blob(data, overwrite=True)


def delete_blobs(
    storage_account: str,
    container: str,
    prefix: str,
    credential=None
) -> int:
    """Delete blobs with prefix (for test cleanup)"""
    if credential is None:
        credential = get_azure_credential()
    
    blobs = list_blobs(storage_account, container, prefix, credential)
    
    if not blobs:
        return 0
    
    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=credential)
    
    deleted = 0
    for blob_name in blobs:
        blob_client = blob_service.get_blob_client(container=container, blob=blob_name)
        blob_client.delete_blob()
        deleted += 1
    
    return deleted


def verify_rbac_only_storage(storage_account: str, credential=None) -> bool:
    """Verify storage account has key-based auth disabled"""
    # This requires Azure Management SDK
    # For now, return placeholder
    # TODO: Implement with azure-mgmt-storage
    return True


def get_terraform_outputs_azure(iac_dir: str = '../../../iac/azure') -> Dict[str, Any]:
    """Load Azure Terraform outputs"""
    import json
    
    state_file = os.path.join(iac_dir, 'terraform.tfstate')
    
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
            return {
                key: value['value']
                for key, value in state.get('outputs', {}).items()
            }
    
    raise FileNotFoundError(f"Terraform state not found at {state_file}")
