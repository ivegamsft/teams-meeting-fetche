variable "bot_name" {
  description = "Name of the Azure Bot Service resource"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "sku" {
  description = "Bot Service SKU (F0 for free, S1 for standard)"
  type        = string
  default     = "F0"
}

variable "microsoft_app_id" {
  description = "Microsoft App ID (from Azure AD app registration)"
  type        = string
}

variable "microsoft_app_type" {
  description = "Microsoft App type (SingleTenant, MultiTenant, UserAssignedMSI)"
  type        = string
  default     = "SingleTenant"
}

variable "microsoft_app_tenant_id" {
  description = "Azure AD tenant ID for SingleTenant apps"
  type        = string
}

variable "app_insights_key" {
  description = "Application Insights instrumentation key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "app_insights_app_id" {
  description = "Application Insights application ID"
  type        = string
  default     = ""
}

variable "messaging_endpoint" {
  description = "HTTPS messaging endpoint for the bot (e.g. API Gateway URL + /bot/messages)"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID for diagnostic settings (empty to skip)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to bot service resources"
  type        = map(string)
  default     = {}
}
