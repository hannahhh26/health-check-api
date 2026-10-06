output "api_url" {
  description = "Local URL of the health-check API."
  value       = "http://${docker_container.health_check_api.ports[0].ip}:${docker_container.health_check_api.ports[0].external}"
}