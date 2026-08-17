variable "name" {
  description = "Name prefix applied to all network resources (e.g. \"stayz3ro-dev\")."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.30.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block."
  }
}

variable "azs" {
  description = "Availability zones to spread subnets across."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets. One per AZ, in order."
  type        = list(string)
  default     = ["10.30.0.0/24", "10.30.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets. One per AZ, in order."
  type        = list(string)
  default     = ["10.30.10.0/24", "10.30.11.0/24"]
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
  default     = {}
}
