resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 5
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "scale_out" {
  name               = "${local.name_prefix}-scale-out"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 60
    metric_aggregation_type = "Maximum"

    step_adjustment {
      metric_interval_lower_bound = 0
      scaling_adjustment          = 1
    }
  }
}

resource "aws_appautoscaling_policy" "scale_in" {
  name               = "${local.name_prefix}-scale-in"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 120
    metric_aggregation_type = "Maximum"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = -1
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "concurrent_requests_high" {
  alarm_name          = "${local.name_prefix}-concurrent-requests-high"
  alarm_description   = "Scale out when concurrent requests exceed the target"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  threshold           = 20
  period              = 60
  namespace           = "ReliablePipeline"
  metric_name         = "ConcurrentRequests"
  statistic           = "Maximum"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.app.name
  }

  alarm_actions      = [aws_appautoscaling_policy.scale_out.arn]
  treat_missing_data = "notBreaching"

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "concurrent_requests_low" {
  alarm_name          = "${local.name_prefix}-concurrent-requests-low"
  alarm_description   = "Scale in when concurrent requests are low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  threshold           = 5
  period              = 60
  namespace           = "ReliablePipeline"
  metric_name         = "ConcurrentRequests"
  statistic           = "Maximum"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.app.name
  }

  alarm_actions      = [aws_appautoscaling_policy.scale_in.arn]
  treat_missing_data = "notBreaching"

  tags = local.common_tags
}