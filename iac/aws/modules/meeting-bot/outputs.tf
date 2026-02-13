output "function_name" {
  description = "Meeting bot Lambda function name"
  value       = aws_lambda_function.meeting_bot.function_name
}

output "function_arn" {
  description = "Meeting bot Lambda function ARN"
  value       = aws_lambda_function.meeting_bot.arn
}

output "webhook_url" {
  description = "Lambda Function URL for direct webhook invocation"
  value       = aws_lambda_function_url.meeting_bot_webhook.function_url
}

output "meetings_table_name" {
  description = "DynamoDB table name for bot sessions"
  value       = aws_dynamodb_table.meeting_bot_sessions.name
}

output "meetings_table_arn" {
  description = "DynamoDB table ARN for bot sessions"
  value       = aws_dynamodb_table.meeting_bot_sessions.arn
}
