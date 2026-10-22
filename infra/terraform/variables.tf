variable "project_name" {
  description = "Name used to identify project resources"
  type        = string
  default     = "reliable-pipeline"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "demo"
}

variable "container_port" {
  description = "Port exposed by the application container"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "CPU units allocated to the ECS Fargate task"
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Memory in MiB allocated to the ECS Fargate task"
  type        = number
  default     = 1024
}

variable "container_image" {
  description = "Full URI of the application container image in ECR"
  type        = string

  validation {
    condition     = can(regex("\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com/", var.container_image))
    error_message = "Provide a real Amazon ECR image URI, including the repository name and image tag."
  }
}