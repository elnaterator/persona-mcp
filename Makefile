.PHONY: build run run-local lint test check format tf-lint tf-check deploy setup help

AWS_REGION ?= us-west-2

help:
	@echo "Root Makefile targets:"
	@echo "  setup      - Install all managed dependencies (Python + Node)"
	@echo "  build      - Build frontend then backend"
	@echo "  run        - Start via Docker Compose"
	@echo "  run-local  - Build frontend then run backend locally"
	@echo "  lint       - Lint both frontend and backend"
	@echo "  test       - Test both frontend and backend"
	@echo "  check      - Run lint + test for both + terraform fmt check"
	@echo "  format     - Format both frontend and backend"
	@echo "  tf-lint    - Check Terraform formatting (infra/)"
	@echo "  tf-check   - tf-lint + Checkov security scan (infra/)"
	@echo "  deploy     - Build image, push to ECR, terraform apply (requires ENV=dev|prod)"

setup:
	cd backend && uv sync
	cd frontend && npm ci

build:
	$(MAKE) -C frontend build
	$(MAKE) -C backend build

run:
	docker compose up --build

run-local:
	$(MAKE) -C frontend build
	$(MAKE) -C backend run

lint:
	$(MAKE) -C frontend lint
	$(MAKE) -C backend lint

test:
	$(MAKE) -C frontend test
	$(MAKE) -C backend test

check:
	$(MAKE) -C frontend check
	$(MAKE) -C backend check
	$(MAKE) tf-lint

format:
	$(MAKE) -C frontend format
	$(MAKE) -C backend format

tf-lint:
	terraform fmt -check -recursive infra/

tf-check:
	$(MAKE) tf-lint
	uvx checkov -d infra/ --quiet --compact

# Deploy to AWS: build Docker image, push to ECR, and apply Terraform.
# Usage: make deploy ENV=dev   or   make deploy ENV=prod
deploy:
ifndef ENV
	$(error ENV is required. Usage: make deploy ENV=dev)
endif
	@[ "$(ENV)" = "dev" ] || [ "$(ENV)" = "prod" ] || \
	  { echo "Error: ENV must be 'dev' or 'prod', got '$(ENV)'"; exit 1; }
	@echo "==> [1/5] terraform init (infra/$(ENV))"
	terraform -chdir=infra/$(ENV) init -input=false
	@echo "==> [2/5] ensure ECR repository exists"
	terraform -chdir=infra/$(ENV) apply -target=module.lambda.aws_ecr_repository.app -auto-approve
	@echo "==> [3/5] build and push Docker image to ECR"
	@set -e; \
	  ECR_URL=$$(terraform -chdir=infra/$(ENV) output -raw ecr_repository_url); \
	  ACCOUNT_ID=$$(aws sts get-caller-identity --query Account --output text); \
	  CLERK_PK=$$(aws ssm get-parameter \
	    --name /persona/$(ENV)/clerk_publishable_key \
	    --with-decryption \
	    --query Parameter.Value \
	    --output text \
	    --region $(AWS_REGION)); \
	  aws ecr get-login-password --region $(AWS_REGION) | \
	    docker login --username AWS --password-stdin $${ACCOUNT_ID}.dkr.ecr.$(AWS_REGION).amazonaws.com; \
	  docker buildx build --platform linux/arm64 --provenance=false \
	    --build-arg VITE_CLERK_PUBLISHABLE_KEY=$${CLERK_PK} \
	    --load -t $${ECR_URL}:latest .; \
	  docker push $${ECR_URL}:latest
	@echo "==> [4/5] terraform apply (full)"
	terraform -chdir=infra/$(ENV) apply
	@echo "==> [5/5] force Lambda to pull latest image from ECR"
	@set -e; \
	  ECR_URL=$$(terraform -chdir=infra/$(ENV) output -raw ecr_repository_url); \
	  DIGEST=$$(aws ecr describe-images \
	    --repository-name persona-$(ENV) \
	    --image-ids imageTag=latest \
	    --query 'imageDetails[0].imageDigest' \
	    --output text \
	    --region $(AWS_REGION)); \
	  aws lambda update-function-code \
	    --function-name persona-$(ENV) \
	    --image-uri $${ECR_URL}@$${DIGEST} \
	    --region $(AWS_REGION) \
	    --output json | jq -r '"    updated to " + .CodeSha256'
	@echo ""
	@echo "==> Deployed. Function URL:"
	@terraform -chdir=infra/$(ENV) output -raw lambda_function_url 2>/dev/null || true
