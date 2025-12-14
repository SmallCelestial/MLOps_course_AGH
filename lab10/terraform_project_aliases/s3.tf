# s3.tf

# uses default provider configuration
resource "aws_s3_bucket" "my_bucket" {
  bucket = "terraform-aliases-state" # replace with your own unique name
  tags = {
    Name = "my-bucket"
  }
}

# alias provider specified, it will use its configuration
resource "aws_s3_bucket" "my_bucket_us_west_2" {
  bucket   = "terraform-aliases-state-us-west-2" # replace with your own unique name
  provider = aws.us_west_2
  tags = {
    Name = "my-bucket"
  }
}