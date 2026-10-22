output "application_url" {
  description = "Public URL of the application"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch monitoring dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}