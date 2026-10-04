provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project = "cloud-netlab"
      Env     = "dev"
      Owner   = "stayz3ro"
    }
  }
}

module "network" {
  source = "../../modules/network"

  name                 = "${var.project}-dev"
  vpc_cidr             = var.vpc_cidr
  azs                  = var.azs
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs

  tags = {
    Project = var.project
    Env     = "dev"
  }
}
