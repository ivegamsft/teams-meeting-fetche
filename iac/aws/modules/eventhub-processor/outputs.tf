output "function_name" {
  description = "Event Hub processor Lambda function name"
  value       = aws_lambda_function.eventhub.function_name
}

output "function_arn" {
  description = "Event Hub processor Lambda function ARN"
  value       = aws_lambda_function.eventhub.arn
}
