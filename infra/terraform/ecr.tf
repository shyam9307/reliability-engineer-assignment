resource "aws_ecr_repository" "app" {
  name                 = "reliability-pipeline"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = local.common_tags
}

output "ecr_repository_url" {
  description = "URL of the ECR repository for the application image."
  value       = aws_ecr_repository.app.repository_url
}