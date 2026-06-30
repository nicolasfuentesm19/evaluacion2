import os
import json
import boto3

bucket_name = "evaluacion4cloud.mooo.com"
region = "us-east-1"
source_bucket = "evaluacion2-archivos-app"

s3 = boto3.client('s3', region_name=region)
s3_resource = boto3.resource('s3', region_name=region)

print(f"1. Creando bucket {bucket_name}...")
try:
    s3.create_bucket(Bucket=bucket_name)
except Exception as e:
    print(f"El bucket ya existe o error: {e}")

print("2. Desactivando Block Public Access...")
s3.put_public_access_block(
    Bucket=bucket_name,
    PublicAccessBlockConfiguration={
        'BlockPublicAcls': False,
        'IgnorePublicAcls': False,
        'BlockPublicPolicy': False,
        'RestrictPublicBuckets': False
    }
)

print("3. Aplicando Bucket Policy para acceso público...")
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
        }
    ]
}
s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))

print("4. Habilitando Static Website Hosting...")
s3.put_bucket_website(
    Bucket=bucket_name,
    WebsiteConfiguration={
        'ErrorDocument': {'Key': 'index.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }
)

print("5. Sincronizando archivos del bucket antiguo...")
os.system(f"aws s3 sync s3://{source_bucket} s3://{bucket_name}")

print(f"\n¡LISTO! Endpoint del website:")
print(f"{bucket_name}.s3-website-{region}.amazonaws.com")
