terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = "npipe:////.//pipe//docker_engine"
}

resource "docker_container" "health_check_api" {
  name  = "health-check-api-terraform"
  image = "health-check-api:1.1.0"

  env = [
    "APP_ENV=${var.app_env}"
  ]

  ports {
    internal = 8000
    external = 8001
    ip       = "127.0.0.1"
  }
}