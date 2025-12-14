variable "bucket_name_prefix" {
  type    = string
  default = "terraform-mlops-state"
}

variable "region" {
   type    = string
   default = "us-east-1"
}

variable "random_suffix" {
  type        = string
}

variable "lifecycle_days" {
  type        = number
  default     = 90
}

variable "lifecycle_storage_class" {
  type        = string
  default     = "GLACIER"
}
