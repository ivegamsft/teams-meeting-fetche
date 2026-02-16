output "bot_service_name" {
  description = "Azure Bot Service resource name"
  value       = azurerm_bot_service_azure_bot.main.name
}

output "bot_service_id" {
  description = "Azure Bot Service resource ID"
  value       = azurerm_bot_service_azure_bot.main.id
}

output "bot_messaging_endpoint" {
  description = "Bot messaging endpoint URL"
  value       = azurerm_bot_service_azure_bot.main.endpoint
}
