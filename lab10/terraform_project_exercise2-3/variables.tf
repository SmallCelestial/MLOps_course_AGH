
variable "regions" {
   type    = list(string)
   default = ["us-east-1", "us-west-2"] # define your regions
}

variable "bucket_name_prefix" {
  type    = string
  default = "terraform-mlops-state" # define your bucket prefixes
}