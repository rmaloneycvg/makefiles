# AWS Infrastructure Makefile
# Equivalent to Azure infrastructure automation using AWS CLI
#
# Usage: make <target> [VARIABLE=value]
# Run `make help` for available targets.

SHELL := /bin/bash
.DEFAULT_GOAL := help
ENV_TOOL := python3 scripts/env_tool.py
ENV_GET := python3 scripts/env_tool.py get
BUDGET_HELPER := python3 scripts/budget_helper.py
API_GW_POLICY := python3 scripts/api_gw_policy.py
COGNITO_ROLES := python3 scripts/cognito_roles.py
LAMBDA_ROUTING := python3 scripts/lambda_routing.py

# Load .env if present
-include .env
export

# Common tags applied to all resources
PROJECT_TAG ?= my-project
ENV_TAG ?= dev
TAGS = Key=Project,Value=$(PROJECT_TAG) Key=Environment,Value=$(ENV_TAG)

# Region
AWS_REGION ?= us-east-1

##@ Help

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m [VARIABLE=value]\n"} \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } \
		/^[a-zA-Z0-9_-]+:.*?## / { printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@ Account & Tags

.PHONY: show-account
show-account: ## Show current AWS account info and save to .env
	$(eval ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text))
	$(eval REGION := $(shell aws configure get region || echo $(AWS_REGION)))
	@echo "Account: $(ACCOUNT_ID) | Region: $(REGION)"
	@$(ENV_TOOL) set ACCOUNT_ID=$(ACCOUNT_ID)
	@$(ENV_TOOL) set AWS_REGION=$(REGION)

.PHONY: tag-resources
tag-resources: ## Tag all resources with project tag (requires: env=<value>)
ifndef env
	$(error env is required: make tag-resources env=dev|prod)
endif
	@echo "Tagging resources with Project=$(PROJECT_TAG), Environment=$(env)..."
	@aws resourcegroupstaggingapi get-resources \
		--tag-filters Key=Project,Values=$(PROJECT_TAG) \
		--query 'ResourceTagMappingList[].ResourceARN' --output text | \
		tr '\t' '\n' | while read arn; do \
			aws resourcegroupstaggingapi tag-resources \
				--resource-arn-list "$$arn" \
				--tags Environment=$(env); \
		done
	@echo "✓ Tagged all project resources with Environment=$(env)"

.PHONY: list-resources
list-resources: ## List all resources with project tag
	@aws resourcegroupstaggingapi get-resources \
		--tag-filters Key=Project,Values=$(PROJECT_TAG) \
		--query 'ResourceTagMappingList[].[ResourceARN,Tags[?Key==`Environment`].Value|[0]]' \
		--output table


##@ Secrets Manager

.PHONY: create-secret
create-secret: ## Create a secret (requires: n=<name> v=<value>)
ifndef n
	$(error n is required: make create-secret n=my-secret v=my-value)
endif
ifndef v
	$(error v is required: make create-secret n=my-secret v=my-value)
endif
	@aws secretsmanager create-secret \
		--name "$(n)" \
		--secret-string "$(v)" \
		--tags $(TAGS) \
		--region $(AWS_REGION)
	@echo "✓ Created secret: $(n)"

.PHONY: list-secrets
list-secrets: ## List all secrets
	@aws secretsmanager list-secrets \
		--query 'SecretList[].[Name,CreatedDate]' \
		--output table --region $(AWS_REGION)

.PHONY: show-secret
show-secret: ## Show secret value (requires: n=<name>)
ifndef n
	$(error n is required: make show-secret n=my-secret)
endif
	@aws secretsmanager get-secret-value \
		--secret-id "$(n)" \
		--query SecretString --output text --region $(AWS_REGION)

.PHONY: update-secret
update-secret: ## Update a secret (requires: n=<name> v=<value>)
ifndef n
	$(error n is required)
endif
ifndef v
	$(error v is required)
endif
	@aws secretsmanager put-secret-value \
		--secret-id "$(n)" \
		--secret-string "$(v)" --region $(AWS_REGION)
	@echo "✓ Updated secret: $(n)"

.PHONY: delete-secret
delete-secret: ## Delete a secret with recovery window (requires: n=<name>)
ifndef n
	$(error n is required: make delete-secret n=my-secret)
endif
	@aws secretsmanager delete-secret \
		--secret-id "$(n)" \
		--recovery-window-in-days 30 --region $(AWS_REGION)
	@echo "✓ Scheduled deletion: $(n) (30-day recovery)"

.PHONY: purge-secret
purge-secret: ## Force delete secret immediately (requires: n=<name>)
ifndef n
	$(error n is required)
endif
	@aws secretsmanager delete-secret \
		--secret-id "$(n)" \
		--force-delete-without-recovery --region $(AWS_REGION)
	@echo "✓ Permanently deleted: $(n)"

##@ KMS Keys

.PHONY: create-kms-key
create-kms-key: ## Create a KMS key (requires: n=<alias>)
ifndef n
	$(error n is required: make create-kms-key n=my-key)
endif
	$(eval KEY_ID := $(shell aws kms create-key \
		--description "$(n)" \
		--tags TagKey=Project,TagValue=$(PROJECT_TAG) TagKey=Environment,TagValue=$(ENV_TAG) \
		--query KeyMetadata.KeyId --output text --region $(AWS_REGION)))
	@aws kms create-alias \
		--alias-name "alias/$(n)" \
		--target-key-id $(KEY_ID) --region $(AWS_REGION)
	@$(ENV_TOOL) set KMS_KEY_ID=$(KEY_ID)
	@echo "✓ Created KMS key: alias/$(n) ($(KEY_ID))"

.PHONY: list-kms-keys
list-kms-keys: ## List KMS key aliases
	@aws kms list-aliases \
		--query 'Aliases[?starts_with(AliasName,`alias/`)].[AliasName,TargetKeyId]' \
		--output table --region $(AWS_REGION)

.PHONY: delete-kms-key
delete-kms-key: ## Schedule KMS key deletion (requires: n=<alias>)
ifndef n
	$(error n is required)
endif
	$(eval KEY_ID := $(shell aws kms describe-key --key-id alias/$(n) --query KeyMetadata.KeyId --output text --region $(AWS_REGION)))
	@aws kms schedule-key-deletion --key-id $(KEY_ID) --pending-window-in-days 30 --region $(AWS_REGION)
	@echo "✓ Scheduled deletion for alias/$(n) in 30 days"


##@ .env Backup/Restore

.PHONY: backup-env
backup-env: ## Backup .env to Secrets Manager
	@aws secretsmanager create-secret \
		--name "env-backup-$(PROJECT_TAG)" \
		--secret-string file://.env \
		--tags $(TAGS) \
		--region $(AWS_REGION) 2>/dev/null || \
	aws secretsmanager put-secret-value \
		--secret-id "env-backup-$(PROJECT_TAG)" \
		--secret-string file://.env --region $(AWS_REGION)
	@echo "✓ Backed up .env to Secrets Manager"

.PHONY: restore-env
restore-env: ## Restore .env from Secrets Manager
	@aws secretsmanager get-secret-value \
		--secret-id "env-backup-$(PROJECT_TAG)" \
		--query SecretString --output text --region $(AWS_REGION) | \
		$(ENV_TOOL) restore-from-stdin
	@echo "✓ Restored .env from Secrets Manager"

##@ S3 Storage

.PHONY: create-s3
create-s3: ## Create S3 bucket (requires: BUCKET_NAME, env=dev|prod|disaster, use=web|lambda|data)
ifndef BUCKET_NAME
	$(error BUCKET_NAME is required)
endif
ifndef env
	$(error env is required: dev|prod|disaster)
endif
ifndef use
	$(error use is required: web|lambda|data)
endif
	@aws s3api create-bucket \
		--bucket $(BUCKET_NAME) \
		--region $(AWS_REGION) \
		$(if $(filter us-east-1,$(AWS_REGION)),,--create-bucket-configuration LocationConstraint=$(AWS_REGION))
	@aws s3api put-bucket-tagging --bucket $(BUCKET_NAME) \
		--tagging 'TagSet=[{Key=Project,Value=$(PROJECT_TAG)},{Key=Environment,Value=$(env)},{Key=Use,Value=$(use)}]'
	@# Encryption
	@aws s3api put-bucket-encryption --bucket $(BUCKET_NAME) \
		--server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
	@# Versioning for prod/disaster
	@if [ "$(env)" != "dev" ]; then \
		aws s3api put-bucket-versioning --bucket $(BUCKET_NAME) \
			--versioning-configuration Status=Enabled; \
	fi
	@# Static website hosting for web use
	@if [ "$(use)" = "web" ]; then \
		aws s3api delete-public-access-block --bucket $(BUCKET_NAME) 2>/dev/null || true; \
		aws s3api put-bucket-policy --bucket $(BUCKET_NAME) --policy '{"Version":"2012-10-17","Statement":[{"Sid":"PublicReadGetObject","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::$(BUCKET_NAME)/*"}]}'; \
		aws s3api put-bucket-website --bucket $(BUCKET_NAME) --website-configuration '{"IndexDocument":{"Suffix":"index.html"},"ErrorDocument":{"Key":"index.html"}}'; \
		echo "  Note: For production, prefer CloudFront + Origin Access Control (private bucket)."; \
	fi
	@$(ENV_TOOL) set BUCKET_NAME_$(use)=$(BUCKET_NAME)
	@echo "✓ Created S3 bucket: $(BUCKET_NAME) (env=$(env), use=$(use))"

.PHONY: delete-s3
delete-s3: ## Delete S3 bucket and contents (requires: BUCKET_NAME)
ifndef BUCKET_NAME
	$(error BUCKET_NAME is required)
endif
	@aws s3 rb s3://$(BUCKET_NAME) --force --region $(AWS_REGION)
	@echo "✓ Deleted bucket: $(BUCKET_NAME)"


##@ Lambda Functions

.PHONY: create-lambda-role
create-lambda-role: ## Create Lambda execution IAM role (requires: LAMBDA_ROLE_NAME)
ifndef LAMBDA_ROLE_NAME
	$(error LAMBDA_ROLE_NAME is required)
endif
	$(eval ROLE_ARN := $(shell aws iam create-role \
		--role-name $(LAMBDA_ROLE_NAME) \
		--assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
		--tags Key=Project,Value=$(PROJECT_TAG) Key=Environment,Value=$(ENV_TAG) \
		--query Role.Arn --output text))
	@aws iam attach-role-policy \
		--role-name $(LAMBDA_ROLE_NAME) \
		--policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
	@aws iam attach-role-policy \
		--role-name $(LAMBDA_ROLE_NAME) \
		--policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
	@$(ENV_TOOL) set LAMBDA_ROLE_ARN=$(ROLE_ARN)
	@echo "✓ Created Lambda role: $(LAMBDA_ROLE_NAME) ($(ROLE_ARN))"

.PHONY: create-lambda
create-lambda: ## Create Lambda function (requires: FUNC_NAME, runtime=python3.12|nodejs20.x|dotnet8, LAMBDA_ROLE_NAME)
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
ifndef runtime
	$(error runtime is required: python3.12|nodejs20.x|dotnet8)
endif
ifndef LAMBDA_ROLE_NAME
	$(error LAMBDA_ROLE_NAME is required)
endif
	$(eval ROLE_ARN := $(shell aws iam get-role --role-name $(LAMBDA_ROLE_NAME) --query Role.Arn --output text))
	@echo "Creating Lambda function: $(FUNC_NAME) ($(runtime))..."
	@aws lambda create-function \
		--function-name $(FUNC_NAME) \
		--runtime $(runtime) \
		--role $(ROLE_ARN) \
		--handler index.handler \
		--zip-file fileb://function.zip \
		--timeout 30 \
		--memory-size 256 \
		--tags Project=$(PROJECT_TAG),Environment=$(ENV_TAG) \
		--region $(AWS_REGION)
	$(eval FUNC_ARN := $(shell aws lambda get-function --function-name $(FUNC_NAME) --query Configuration.FunctionArn --output text --region $(AWS_REGION)))
	@$(ENV_TOOL) set LAMBDA_ARN_$(FUNC_NAME)=$(FUNC_ARN)
	@echo "✓ Created Lambda: $(FUNC_NAME)"

.PHONY: deploy-lambda
deploy-lambda: ## Deploy Lambda code from zip (requires: FUNC_NAME)
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
	@aws lambda update-function-code \
		--function-name $(FUNC_NAME) \
		--zip-file fileb://function.zip \
		--region $(AWS_REGION)
	@echo "✓ Deployed code to: $(FUNC_NAME)"

.PHONY: create-lambda-alias
create-lambda-alias: ## Create Lambda alias for blue/green (requires: FUNC_NAME, n=<alias>)
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
ifndef n
	$(error n is required: make create-lambda-alias FUNC_NAME=x n=live)
endif
	$(eval VERSION := $(shell aws lambda publish-version --function-name $(FUNC_NAME) --query Version --output text --region $(AWS_REGION)))
	@aws lambda create-alias \
		--function-name $(FUNC_NAME) \
		--name $(n) \
		--function-version $(VERSION) \
		--region $(AWS_REGION)
	@echo "✓ Created alias $(n) → version $(VERSION)"

.PHONY: shift-traffic
shift-traffic: ## Shift traffic between Lambda versions (requires: FUNC_NAME, n=<alias>, weight=<0-100>)
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
ifndef n
	$(error n is required)
endif
ifndef weight
	$(error weight is required: 0-100 percent to new version)
endif
	@LATEST=$$(aws lambda publish-version --function-name $(FUNC_NAME) --query Version --output text --region $(AWS_REGION)); \
	CURRENT=$$(aws lambda get-alias --function-name $(FUNC_NAME) --name $(n) --query FunctionVersion --output text --region $(AWS_REGION)); \
	ROUTING=$$($(LAMBDA_ROUTING) --version "$$LATEST" --weight $(weight)); \
	aws lambda update-alias \
		--function-name $(FUNC_NAME) \
		--name $(n) \
		--function-version "$$CURRENT" \
		--routing-config "$$ROUTING" \
		--region $(AWS_REGION); \
	echo "✓ Routing $(weight)% traffic to version $$LATEST (alias $(n), base=$$CURRENT)"


##@ Cognito Auth

.PHONY: create-user-pool
create-user-pool: ## Create Cognito User Pool (requires: POOL_NAME)
ifndef POOL_NAME
	$(error POOL_NAME is required)
endif
	$(eval POOL_ID := $(shell aws cognito-idp create-user-pool \
		--pool-name $(POOL_NAME) \
		--auto-verified-attributes email \
		--username-attributes email \
		--mfa-configuration OFF \
		--user-pool-tags Project=$(PROJECT_TAG),Environment=$(ENV_TAG) \
		--query UserPool.Id --output text --region $(AWS_REGION)))
	@$(ENV_TOOL) set COGNITO_POOL_ID=$(POOL_ID)
	@echo "✓ Created User Pool: $(POOL_NAME) ($(POOL_ID))"

.PHONY: create-user-pool-client
create-user-pool-client: ## Create User Pool app client (requires: CLIENT_NAME; optional: callback=<url> logout=<url>)
ifndef CLIENT_NAME
	$(error CLIENT_NAME is required)
endif
	$(eval POOL_ID := $(shell $(ENV_GET) COGNITO_POOL_ID))
	@if [ -z "$(POOL_ID)" ]; then echo "❌ COGNITO_POOL_ID not set. Run create-user-pool first."; exit 1; fi
	@if [ -n "$(callback)" ]; then \
		CLIENT_ID=$$(aws cognito-idp create-user-pool-client \
			--user-pool-id $(POOL_ID) --client-name $(CLIENT_NAME) \
			--no-generate-secret \
			--explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
			--supported-identity-providers COGNITO \
			--callback-urls "$(callback)" \
			--logout-urls "$(if $(logout),$(logout),$(callback))" \
			--allowed-o-auth-flows code \
			--allowed-o-auth-scopes email openid profile \
			--allowed-o-auth-flows-user-pool-client \
			--query UserPoolClient.ClientId --output text --region $(AWS_REGION)); \
	else \
		CLIENT_ID=$$(aws cognito-idp create-user-pool-client \
			--user-pool-id $(POOL_ID) --client-name $(CLIENT_NAME) \
			--no-generate-secret \
			--explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
			--supported-identity-providers COGNITO \
			--query UserPoolClient.ClientId --output text --region $(AWS_REGION)); \
	fi; \
	$(ENV_TOOL) set COGNITO_CLIENT_ID=$$CLIENT_ID; \
	echo "✓ Created app client: $(CLIENT_NAME) ($$CLIENT_ID)"

.PHONY: create-user-pool-domain
create-user-pool-domain: ## Create hosted UI domain (requires: DOMAIN_PREFIX)
ifndef DOMAIN_PREFIX
	$(error DOMAIN_PREFIX is required)
endif
	$(eval POOL_ID := $(shell $(ENV_GET) COGNITO_POOL_ID))
	@aws cognito-idp create-user-pool-domain \
		--user-pool-id $(POOL_ID) \
		--domain $(DOMAIN_PREFIX) --region $(AWS_REGION)
	@$(ENV_TOOL) set COGNITO_DOMAIN=$(DOMAIN_PREFIX).auth.$(AWS_REGION).amazoncognito.com
	@echo "✓ Created domain: $(DOMAIN_PREFIX).auth.$(AWS_REGION).amazoncognito.com"

.PHONY: create-cognito-groups
create-cognito-groups: ## Create standard groups (Reader, Writer, Admin)
	$(eval POOL_ID := $(shell $(ENV_GET) COGNITO_POOL_ID))
	@$(COGNITO_ROLES) create-groups --user-pool-id $(POOL_ID)
	@echo "✓ Created Cognito groups"

.PHONY: assign-user-group
assign-user-group: ## Add user to group (requires: username=<email> group=<Reader|Writer|Admin>)
ifndef username
	$(error username is required)
endif
ifndef group
	$(error group is required: Reader|Writer|Admin)
endif
	$(eval POOL_ID := $(shell $(ENV_GET) COGNITO_POOL_ID))
	@$(COGNITO_ROLES) assign-user --user-pool-id $(POOL_ID) --username $(username) --group $(group)


##@ API Gateway

.PHONY: create-api-gw
create-api-gw: ## Create HTTP API Gateway (requires: API_NAME)
ifndef API_NAME
	$(error API_NAME is required)
endif
	$(eval API_ID := $(shell aws apigatewayv2 create-api \
		--name $(API_NAME) \
		--protocol-type HTTP \
		--tags Project=$(PROJECT_TAG),Environment=$(ENV_TAG) \
		--query ApiId --output text --region $(AWS_REGION)))
	@$(ENV_TOOL) set API_GW_ID=$(API_ID)
	@echo "✓ Created HTTP API: $(API_NAME) ($(API_ID))"

.PHONY: api-gw-add-authorizer
api-gw-add-authorizer: ## Add JWT authorizer pointing to Cognito
	$(eval API_ID := $(shell $(ENV_GET) API_GW_ID))
	$(eval POOL_ID := $(shell $(ENV_GET) COGNITO_POOL_ID))
	$(eval CLIENT_ID := $(shell $(ENV_GET) COGNITO_CLIENT_ID))
	@if [ -z "$(API_ID)" ] || [ -z "$(POOL_ID)" ] || [ -z "$(CLIENT_ID)" ]; then \
		echo "❌ API_GW_ID / COGNITO_POOL_ID / COGNITO_CLIENT_ID missing from .env"; exit 1; \
	fi
	@$(API_GW_POLICY) jwt-authorizer \
		--client-id $(CLIENT_ID) --user-pool-id $(POOL_ID) --region $(AWS_REGION) \
		> .tmp-authorizer.json
	$(eval AUTH_ID := $(shell aws apigatewayv2 create-authorizer \
		--api-id $(API_ID) \
		--name CognitoAuthorizer \
		--authorizer-type JWT \
		--identity-source '$$request.header.Authorization' \
		--jwt-configuration Audience=$(CLIENT_ID),Issuer=https://cognito-idp.$(AWS_REGION).amazonaws.com/$(POOL_ID) \
		--query AuthorizerId --output text --region $(AWS_REGION)))
	@rm -f .tmp-authorizer.json
	@$(ENV_TOOL) set API_GW_AUTHORIZER_ID=$(AUTH_ID)
	@echo "✓ Created JWT authorizer: $(AUTH_ID)"

.PHONY: api-gw-add-lambda
api-gw-add-lambda: ## Integrate Lambda with API Gateway (requires: FUNC_NAME, path=<route>, method=<GET|POST|...>)
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
ifndef path
	$(error path is required: make api-gw-add-lambda FUNC_NAME=x path=/items method=GET)
endif
	$(eval method ?= GET)
	$(eval API_ID := $(shell $(ENV_GET) API_GW_ID))
	$(eval AUTH_ID := $(shell $(ENV_GET) API_GW_AUTHORIZER_ID))
	$(eval FUNC_ARN := $(shell aws lambda get-function --function-name $(FUNC_NAME) --query Configuration.FunctionArn --output text --region $(AWS_REGION)))
	$(eval INTEG_ID := $(shell aws apigatewayv2 create-integration \
		--api-id $(API_ID) \
		--integration-type AWS_PROXY \
		--integration-uri $(FUNC_ARN) \
		--payload-format-version 2.0 \
		--query IntegrationId --output text --region $(AWS_REGION)))
	@aws apigatewayv2 create-route \
		--api-id $(API_ID) \
		--route-key "$(method) $(path)" \
		--authorization-type JWT \
		--authorizer-id $(AUTH_ID) \
		--target integrations/$(INTEG_ID) \
		--region $(AWS_REGION)
	@aws lambda add-permission \
		--function-name $(FUNC_NAME) \
		--statement-id apigw-$(FUNC_NAME)-$(method) \
		--action lambda:InvokeFunction \
		--principal apigateway.amazonaws.com \
		--source-arn "arn:aws:execute-api:$(AWS_REGION):$(shell aws sts get-caller-identity --query Account --output text):$(API_ID)/*/*" \
		--region $(AWS_REGION) 2>/dev/null || true
	@echo "✓ Added route: $(method) $(path) → $(FUNC_NAME)"

.PHONY: api-gw-deploy
api-gw-deploy: ## Deploy API Gateway stage (requires: stage=<name>)
ifndef stage
	$(error stage is required: make api-gw-deploy stage=prod)
endif
	$(eval API_ID := $(shell $(ENV_GET) API_GW_ID))
	@aws apigatewayv2 create-stage \
		--api-id $(API_ID) \
		--stage-name $(stage) \
		--auto-deploy \
		--region $(AWS_REGION) 2>/dev/null || \
	aws apigatewayv2 update-stage \
		--api-id $(API_ID) \
		--stage-name $(stage) \
		--auto-deploy \
		--region $(AWS_REGION)
	@echo "✓ Deployed stage: $(stage)"
	@echo "  URL: https://$(API_ID).execute-api.$(AWS_REGION).amazonaws.com/$(stage)"

.PHONY: api-gw-cors
api-gw-cors: ## Configure CORS on API Gateway (requires: origin=<url>)
ifndef origin
	$(error origin is required: make api-gw-cors origin=https://example.com)
endif
	$(eval API_ID := $(shell $(ENV_GET) API_GW_ID))
	$(eval CORS_JSON := $(shell $(API_GW_POLICY) cors-config --origins $(origin)))
	@aws apigatewayv2 update-api \
		--api-id $(API_ID) \
		--cors-configuration '$(CORS_JSON)' \
		--region $(AWS_REGION)
	@echo "✓ Configured CORS for: $(origin)"

.PHONY: api-gw-throttle
api-gw-throttle: ## Set rate limiting (requires: rate=<req/s> burst=<N>)
ifndef rate
	$(error rate is required)
endif
ifndef burst
	$(error burst is required)
endif
	$(eval API_ID := $(shell $(ENV_GET) API_GW_ID))
	@aws apigatewayv2 update-stage \
		--api-id $(API_ID) \
		--stage-name '$$default' \
		--default-route-settings '{"ThrottlingBurstLimit":$(burst),"ThrottlingRateLimit":$(rate).0}' \
		--region $(AWS_REGION)
	@echo "✓ Rate limit: $(rate) req/s, burst=$(burst)"


##@ VPC & Networking

.PHONY: create-vpc
create-vpc: ## Create VPC with public/private subnets (requires: VPC_NAME)
ifndef VPC_NAME
	$(error VPC_NAME is required)
endif
	$(eval VPC_ID := $(shell aws ec2 create-vpc \
		--cidr-block 10.0.0.0/16 \
		--tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=$(VPC_NAME)},{Key=Project,Value=$(PROJECT_TAG)},{Key=Environment,Value=$(ENV_TAG)}]' \
		--query Vpc.VpcId --output text --region $(AWS_REGION)))
	@aws ec2 modify-vpc-attribute --vpc-id $(VPC_ID) --enable-dns-hostnames '{"Value":true}' --region $(AWS_REGION)
	$(eval PUB_SUBNET := $(shell aws ec2 create-subnet \
		--vpc-id $(VPC_ID) --cidr-block 10.0.1.0/24 --availability-zone $(AWS_REGION)a \
		--tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=$(VPC_NAME)-public},{Key=Tier,Value=public}]' \
		--query Subnet.SubnetId --output text --region $(AWS_REGION)))
	$(eval PRIV_SUBNET_1 := $(shell aws ec2 create-subnet \
		--vpc-id $(VPC_ID) --cidr-block 10.0.2.0/24 --availability-zone $(AWS_REGION)a \
		--tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=$(VPC_NAME)-private-a},{Key=Tier,Value=private}]' \
		--query Subnet.SubnetId --output text --region $(AWS_REGION)))
	$(eval PRIV_SUBNET_2 := $(shell aws ec2 create-subnet \
		--vpc-id $(VPC_ID) --cidr-block 10.0.3.0/24 --availability-zone $(AWS_REGION)b \
		--tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=$(VPC_NAME)-private-b},{Key=Tier,Value=private}]' \
		--query Subnet.SubnetId --output text --region $(AWS_REGION)))
	$(eval IGW_ID := $(shell aws ec2 create-internet-gateway \
		--tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=$(VPC_NAME)-igw}]' \
		--query InternetGateway.InternetGatewayId --output text --region $(AWS_REGION)))
	@aws ec2 attach-internet-gateway --internet-gateway-id $(IGW_ID) --vpc-id $(VPC_ID) --region $(AWS_REGION)
	@$(ENV_TOOL) set VPC_ID=$(VPC_ID)
	@$(ENV_TOOL) set PUBLIC_SUBNET=$(PUB_SUBNET)
	@$(ENV_TOOL) set PRIVATE_SUBNET_1=$(PRIV_SUBNET_1)
	@$(ENV_TOOL) set PRIVATE_SUBNET_2=$(PRIV_SUBNET_2)
	@echo "✓ Created VPC: $(VPC_NAME) ($(VPC_ID))"
	@echo "  Public:  $(PUB_SUBNET)"
	@echo "  Private: $(PRIV_SUBNET_1), $(PRIV_SUBNET_2)"

.PHONY: create-vpc-endpoint
create-vpc-endpoint: ## Create VPC endpoint for AWS service (requires: service=<s3|secretsmanager|dynamodb>)
ifndef service
	$(error service is required: s3|secretsmanager|dynamodb|sqs)
endif
	$(eval VPC_ID := $(shell $(ENV_GET) VPC_ID))
	$(eval PRIV_SUBNET_1 := $(shell $(ENV_GET) PRIVATE_SUBNET_1))
	$(eval PRIV_SUBNET_2 := $(shell $(ENV_GET) PRIVATE_SUBNET_2))
	@if [ "$(service)" = "s3" ] || [ "$(service)" = "dynamodb" ]; then \
		aws ec2 create-vpc-endpoint \
			--vpc-id $(VPC_ID) \
			--service-name com.amazonaws.$(AWS_REGION).$(service) \
			--vpc-endpoint-type Gateway \
			--tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Project,Value=$(PROJECT_TAG)}]' \
			--region $(AWS_REGION); \
	else \
		aws ec2 create-vpc-endpoint \
			--vpc-id $(VPC_ID) \
			--service-name com.amazonaws.$(AWS_REGION).$(service) \
			--vpc-endpoint-type Interface \
			--subnet-ids $(PRIV_SUBNET_1) $(PRIV_SUBNET_2) \
			--private-dns-enabled \
			--tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Project,Value=$(PROJECT_TAG)}]' \
			--region $(AWS_REGION); \
	fi
	@echo "✓ Created VPC endpoint for: $(service)"

.PHONY: lambda-vpc-config
lambda-vpc-config: ## Attach Lambda to VPC private subnets (requires: FUNC_NAME)
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
	$(eval PRIV_SUBNET_1 := $(shell $(ENV_GET) PRIVATE_SUBNET_1))
	$(eval PRIV_SUBNET_2 := $(shell $(ENV_GET) PRIVATE_SUBNET_2))
	$(eval SG_ID := $(shell aws ec2 describe-security-groups \
		--filters Name=vpc-id,Values=$(shell $(ENV_GET) VPC_ID) Name=group-name,Values=default \
		--query 'SecurityGroups[0].GroupId' --output text --region $(AWS_REGION)))
	@aws lambda update-function-configuration \
		--function-name $(FUNC_NAME) \
		--vpc-config SubnetIds=$(PRIV_SUBNET_1),$(PRIV_SUBNET_2),SecurityGroupIds=$(SG_ID) \
		--region $(AWS_REGION)
	@echo "✓ Attached $(FUNC_NAME) to VPC private subnets"

##@ CloudFront & WAF

.PHONY: create-cloudfront
create-cloudfront: ## Create CloudFront distribution for S3 website (requires: BUCKET_NAME)
ifndef BUCKET_NAME
	$(error BUCKET_NAME is required)
endif
	$(eval OAC_ID := $(shell aws cloudfront create-origin-access-control \
		--origin-access-control-config '{"Name":"$(BUCKET_NAME)-oac","SigningProtocol":"sigv4","SigningBehavior":"always","OriginAccessControlOriginType":"s3"}' \
		--query OriginAccessControl.Id --output text))
	$(eval DIST_ID := $(shell aws cloudfront create-distribution \
		--distribution-config '{"CallerReference":"$(BUCKET_NAME)-$(shell date +%s)","Origins":{"Quantity":1,"Items":[{"Id":"S3-$(BUCKET_NAME)","DomainName":"$(BUCKET_NAME).s3.$(AWS_REGION).amazonaws.com","OriginAccessControlId":"$(OAC_ID)","S3OriginConfig":{"OriginAccessIdentity":""}}]},"DefaultCacheBehavior":{"TargetOriginId":"S3-$(BUCKET_NAME)","ViewerProtocolPolicy":"redirect-to-https","AllowedMethods":{"Quantity":2,"Items":["GET","HEAD"]},"CachePolicyId":"658327ea-f89d-4fab-a63d-7e88639e58f6","Compress":true},"Enabled":true,"DefaultRootObject":"index.html","Comment":"$(PROJECT_TAG) web distribution"}' \
		--query Distribution.Id --output text))
	@$(ENV_TOOL) set CLOUDFRONT_DIST_ID=$(DIST_ID)
	@$(ENV_TOOL) set CLOUDFRONT_OAC_ID=$(OAC_ID)
	@echo "✓ Created CloudFront distribution: $(DIST_ID)"
	@echo "  Domain: $(shell aws cloudfront get-distribution --id $(DIST_ID) --query Distribution.DomainName --output text)"

.PHONY: create-waf
create-waf: ## Create WAF WebACL with managed rules
	$(eval WAF_ARN := $(shell aws wafv2 create-web-acl \
		--name $(PROJECT_TAG)-waf \
		--scope CLOUDFRONT \
		--default-action '{"Allow":{}}' \
		--rules '[{"Name":"AWSManagedRulesCommonRuleSet","Priority":1,"Statement":{"ManagedRuleGroupStatement":{"VendorName":"AWS","Name":"AWSManagedRulesCommonRuleSet"}},"OverrideAction":{"None":{}},"VisibilityConfig":{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"CommonRules"}},{"Name":"AWSManagedRulesBotControlRuleSet","Priority":2,"Statement":{"ManagedRuleGroupStatement":{"VendorName":"AWS","Name":"AWSManagedRulesBotControlRuleSet"}},"OverrideAction":{"None":{}},"VisibilityConfig":{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"BotControl"}}]' \
		--visibility-config '{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"$(PROJECT_TAG)-waf"}' \
		--region us-east-1 \
		--query Summary.ARN --output text))
	@$(ENV_TOOL) set WAF_ACL_ARN=$(WAF_ARN)
	@echo "✓ Created WAF WebACL: $(WAF_ARN)"

.PHONY: attach-waf
attach-waf: ## Attach WAF to CloudFront distribution
	$(eval WAF_ARN := $(shell $(ENV_GET) WAF_ACL_ARN))
	$(eval DIST_ARN := $(shell aws cloudfront get-distribution --id $(shell $(ENV_GET) CLOUDFRONT_DIST_ID) --query Distribution.ARN --output text))
	@aws wafv2 associate-web-acl \
		--web-acl-arn $(WAF_ARN) \
		--resource-arn $(DIST_ARN) \
		--region us-east-1
	@echo "✓ Attached WAF to CloudFront"

##@ Custom Domain (ACM + Route 53)

.PHONY: request-cert
request-cert: ## Request ACM certificate for custom domain (requires: DOMAIN; CloudFront certs must be in us-east-1)
ifndef DOMAIN
	$(error DOMAIN is required)
endif
	$(eval CERT_REGION := $(or $(CERT_REGION),us-east-1))
	$(eval CERT_ARN := $(shell aws acm request-certificate \
		--domain-name $(DOMAIN) \
		--validation-method DNS \
		--tags Key=Project,Value=$(PROJECT_TAG) \
		--query CertificateArn --output text \
		--region $(CERT_REGION)))
	@$(ENV_TOOL) set ACM_CERT_ARN=$(CERT_ARN)
	@echo "✓ Requested certificate: $(CERT_ARN)"
	@echo "  Validate via DNS: aws acm describe-certificate --certificate-arn $(CERT_ARN) --region $(CERT_REGION) --query Certificate.DomainValidationOptions"

.PHONY: validate-cert-route53
validate-cert-route53: ## Create Route 53 validation records for ACM cert (requires: DOMAIN, HOSTED_ZONE_ID)
ifndef DOMAIN
	$(error DOMAIN is required)
endif
ifndef HOSTED_ZONE_ID
	$(error HOSTED_ZONE_ID is required)
endif
	$(eval CERT_ARN := $(shell $(ENV_GET) ACM_CERT_ARN))
	$(eval CERT_REGION := $(or $(CERT_REGION),us-east-1))
	@VALID=$$(aws acm describe-certificate --certificate-arn $(CERT_ARN) --region $(CERT_REGION) \
		--query 'Certificate.DomainValidationOptions[0].ResourceRecord' --output json); \
	NAME=$$(echo "$$VALID" | python3 -c "import json,sys; print(json.load(sys.stdin)['Name'])"); \
	VALUE=$$(echo "$$VALID" | python3 -c "import json,sys; print(json.load(sys.stdin)['Value'])"); \
	TYPE=$$(echo "$$VALID" | python3 -c "import json,sys; print(json.load(sys.stdin)['Type'])"); \
	aws route53 change-resource-record-sets --hosted-zone-id $(HOSTED_ZONE_ID) \
		--change-batch "{\"Changes\":[{\"Action\":\"UPSERT\",\"ResourceRecordSet\":{\"Name\":\"$$NAME\",\"Type\":\"$$TYPE\",\"TTL\":300,\"ResourceRecords\":[{\"Value\":\"$$VALUE\"}]}}]}"
	@echo "✓ Created Route 53 validation record. Cert will validate in a few minutes."

.PHONY: attach-domain-cloudfront
attach-domain-cloudfront: ## Attach custom domain + ACM cert to CloudFront distribution (requires: DOMAIN)
ifndef DOMAIN
	$(error DOMAIN is required)
endif
	$(eval DIST_ID := $(shell $(ENV_GET) CLOUDFRONT_DIST_ID))
	$(eval CERT_ARN := $(shell $(ENV_GET) ACM_CERT_ARN))
	@if [ -z "$(DIST_ID)" ] || [ -z "$(CERT_ARN)" ]; then \
		echo "❌ CLOUDFRONT_DIST_ID and ACM_CERT_ARN must be in .env"; exit 1; \
	fi
	@echo "⚠️  Attaching custom domains to an existing CloudFront distribution requires"
	@echo "    updating its full config. Use 'aws cloudfront update-distribution' with an"
	@echo "    etag and modified config JSON, or recreate the distribution."
	@echo "    Cert ARN: $(CERT_ARN)"
	@echo "    Distribution: $(DIST_ID)"
	@echo "    Domain alias to add: $(DOMAIN)"

.PHONY: create-dns-alias
create-dns-alias: ## Create Route 53 A-record alias pointing to CloudFront (requires: DOMAIN, HOSTED_ZONE_ID)
ifndef DOMAIN
	$(error DOMAIN is required)
endif
ifndef HOSTED_ZONE_ID
	$(error HOSTED_ZONE_ID is required)
endif
	$(eval DIST_DOMAIN := $(shell aws cloudfront get-distribution --id $(shell $(ENV_GET) CLOUDFRONT_DIST_ID) --query Distribution.DomainName --output text))
	@# Z2FDTNDATAQYW2 is the fixed CloudFront hosted-zone ID for all A-record aliases
	@aws route53 change-resource-record-sets --hosted-zone-id $(HOSTED_ZONE_ID) \
		--change-batch '{"Changes":[{"Action":"UPSERT","ResourceRecordSet":{"Name":"$(DOMAIN)","Type":"A","AliasTarget":{"HostedZoneId":"Z2FDTNDATAQYW2","DNSName":"$(DIST_DOMAIN)","EvaluateTargetHealth":false}}}]}'
	@echo "✓ Created Route 53 alias: $(DOMAIN) → $(DIST_DOMAIN)"

##@ Monitoring & Logging

.PHONY: create-log-group
create-log-group: ## Create CloudWatch log group (requires: n=<name>)
ifndef n
	$(error n is required)
endif
	@aws logs create-log-group \
		--log-group-name $(n) \
		--tags Project=$(PROJECT_TAG),Environment=$(ENV_TAG) \
		--region $(AWS_REGION)
	@aws logs put-retention-policy \
		--log-group-name $(n) \
		--retention-in-days 30 \
		--region $(AWS_REGION)
	@echo "✓ Created log group: $(n) (30-day retention)"

.PHONY: enable-xray
enable-xray: ## Enable X-Ray tracing on Lambda (requires: FUNC_NAME)
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
	@aws lambda update-function-configuration \
		--function-name $(FUNC_NAME) \
		--tracing-config Mode=Active \
		--region $(AWS_REGION)
	@echo "✓ Enabled X-Ray on: $(FUNC_NAME)"

.PHONY: create-alarm
create-alarm: ## Create CloudWatch alarm (requires: FUNC_NAME, metric=<Errors|Duration|Throttles>)
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
ifndef metric
	$(error metric is required: Errors|Duration|Throttles)
endif
	@aws cloudwatch put-metric-alarm \
		--alarm-name "$(FUNC_NAME)-$(metric)" \
		--namespace AWS/Lambda \
		--metric-name $(metric) \
		--dimensions Name=FunctionName,Value=$(FUNC_NAME) \
		--statistic Sum \
		--period 300 \
		--threshold 5 \
		--comparison-operator GreaterThanThreshold \
		--evaluation-periods 1 \
		--treat-missing-data notBreaching \
		--tags Key=Project,Value=$(PROJECT_TAG) \
		--region $(AWS_REGION)
	@echo "✓ Created alarm: $(FUNC_NAME)-$(metric)"


##@ DynamoDB

.PHONY: create-dynamodb
create-dynamodb: ## Create DynamoDB table (requires: TABLE_NAME, pk=<partition-key>, env=dev|prod)
ifndef TABLE_NAME
	$(error TABLE_NAME is required)
endif
ifndef pk
	$(error pk is required: partition key name)
endif
ifndef env
	$(error env is required: dev|prod)
endif
	@if [ "$(env)" = "dev" ]; then \
		aws dynamodb create-table \
			--table-name $(TABLE_NAME) \
			--attribute-definitions AttributeName=$(pk),AttributeType=S \
			--key-schema AttributeName=$(pk),KeyType=HASH \
			--billing-mode PAY_PER_REQUEST \
			--tags Key=Project,Value=$(PROJECT_TAG) Key=Environment,Value=$(env) \
			--region $(AWS_REGION); \
	else \
		aws dynamodb create-table \
			--table-name $(TABLE_NAME) \
			--attribute-definitions AttributeName=$(pk),AttributeType=S \
			--key-schema AttributeName=$(pk),KeyType=HASH \
			--billing-mode PROVISIONED \
			--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
			--tags Key=Project,Value=$(PROJECT_TAG) Key=Environment,Value=$(env) \
			--region $(AWS_REGION); \
	fi
	@echo "✓ Created DynamoDB table: $(TABLE_NAME) (pk=$(pk), env=$(env))"

.PHONY: delete-dynamodb
delete-dynamodb: ## Delete DynamoDB table (requires: TABLE_NAME)
ifndef TABLE_NAME
	$(error TABLE_NAME is required)
endif
	@aws dynamodb delete-table --table-name $(TABLE_NAME) --region $(AWS_REGION)
	@echo "✓ Deleted table: $(TABLE_NAME)"

##@ SQS Queues

.PHONY: create-sqs
create-sqs: ## Create SQS queue (requires: n=<name>, env=dev|prod)
ifndef n
	$(error n is required)
endif
ifndef env
	$(error env is required: dev|prod)
endif
	@if [ "$(env)" = "prod" ]; then \
		aws sqs create-queue \
			--queue-name $(n).fifo \
			--attributes '{"FifoQueue":"true","ContentBasedDeduplication":"true","VisibilityTimeout":"60"}' \
			--tags Project=$(PROJECT_TAG),Environment=$(env) \
			--region $(AWS_REGION); \
	else \
		aws sqs create-queue \
			--queue-name $(n) \
			--attributes '{"VisibilityTimeout":"30"}' \
			--tags Project=$(PROJECT_TAG),Environment=$(env) \
			--region $(AWS_REGION); \
	fi
	@echo "✓ Created SQS queue: $(n) (env=$(env))"

.PHONY: delete-sqs
delete-sqs: ## Delete SQS queue (requires: n=<name>)
ifndef n
	$(error n is required)
endif
	$(eval QUEUE_URL := $(shell aws sqs get-queue-url --queue-name $(n) --query QueueUrl --output text --region $(AWS_REGION)))
	@aws sqs delete-queue --queue-url $(QUEUE_URL) --region $(AWS_REGION)
	@echo "✓ Deleted queue: $(n)"

##@ EventBridge

.PHONY: create-eventbridge-rule
create-eventbridge-rule: ## Create EventBridge rule for S3 events (requires: BUCKET_NAME, FUNC_NAME, n=<rule-name>)
ifndef n
	$(error n is required)
endif
ifndef BUCKET_NAME
	$(error BUCKET_NAME is required)
endif
ifndef FUNC_NAME
	$(error FUNC_NAME is required)
endif
	$(eval FUNC_ARN := $(shell aws lambda get-function --function-name $(FUNC_NAME) --query Configuration.FunctionArn --output text --region $(AWS_REGION)))
	@aws events put-rule \
		--name $(n) \
		--event-pattern '{"source":["aws.s3"],"detail-type":["Object Created"],"detail":{"bucket":{"name":["$(BUCKET_NAME)"]}}}' \
		--tags Key=Project,Value=$(PROJECT_TAG) \
		--region $(AWS_REGION)
	@aws events put-targets \
		--rule $(n) \
		--targets '[{"Id":"lambda-target","Arn":"$(FUNC_ARN)"}]' \
		--region $(AWS_REGION)
	@aws lambda add-permission \
		--function-name $(FUNC_NAME) \
		--statement-id eventbridge-$(n) \
		--action lambda:InvokeFunction \
		--principal events.amazonaws.com \
		--source-arn $(shell aws events describe-rule --name $(n) --query Arn --output text --region $(AWS_REGION)) \
		--region $(AWS_REGION) 2>/dev/null || true
	@echo "✓ Created EventBridge rule: $(n) (S3 → $(FUNC_NAME))"

##@ RDS

.PHONY: create-db-subnet-group
create-db-subnet-group: ## Create RDS DB subnet group from existing private subnets (requires: DB_SUBNET_GROUP)
ifndef DB_SUBNET_GROUP
	$(error DB_SUBNET_GROUP is required)
endif
	$(eval PRIV_SUBNET_1 := $(shell $(ENV_GET) PRIVATE_SUBNET_1))
	$(eval PRIV_SUBNET_2 := $(shell $(ENV_GET) PRIVATE_SUBNET_2))
	@if [ -z "$(PRIV_SUBNET_1)" ] || [ -z "$(PRIV_SUBNET_2)" ]; then \
		echo "❌ Private subnets missing from .env. Run create-vpc first."; exit 1; \
	fi
	@aws rds create-db-subnet-group \
		--db-subnet-group-name $(DB_SUBNET_GROUP) \
		--db-subnet-group-description "Private subnets for $(PROJECT_TAG)" \
		--subnet-ids $(PRIV_SUBNET_1) $(PRIV_SUBNET_2) \
		--tags Key=Project,Value=$(PROJECT_TAG) \
		--region $(AWS_REGION)
	@$(ENV_TOOL) set DB_SUBNET_GROUP=$(DB_SUBNET_GROUP)
	@echo "✓ Created DB subnet group: $(DB_SUBNET_GROUP)"

.PHONY: create-cache-subnet-group
create-cache-subnet-group: ## Create ElastiCache subnet group (requires: CACHE_SUBNET_GROUP)
ifndef CACHE_SUBNET_GROUP
	$(error CACHE_SUBNET_GROUP is required)
endif
	$(eval PRIV_SUBNET_1 := $(shell $(ENV_GET) PRIVATE_SUBNET_1))
	$(eval PRIV_SUBNET_2 := $(shell $(ENV_GET) PRIVATE_SUBNET_2))
	@if [ -z "$(PRIV_SUBNET_1)" ] || [ -z "$(PRIV_SUBNET_2)" ]; then \
		echo "❌ Private subnets missing from .env. Run create-vpc first."; exit 1; \
	fi
	@aws elasticache create-cache-subnet-group \
		--cache-subnet-group-name $(CACHE_SUBNET_GROUP) \
		--cache-subnet-group-description "Private subnets for $(PROJECT_TAG)" \
		--subnet-ids $(PRIV_SUBNET_1) $(PRIV_SUBNET_2) \
		--region $(AWS_REGION)
	@$(ENV_TOOL) set CACHE_SUBNET_GROUP=$(CACHE_SUBNET_GROUP)
	@echo "✓ Created cache subnet group: $(CACHE_SUBNET_GROUP)"

.PHONY: create-rds
create-rds: ## Create RDS PostgreSQL instance (requires: DB_NAME, env=dev|prod, DB_SUBNET_GROUP)
ifndef DB_NAME
	$(error DB_NAME is required)
endif
ifndef env
	$(error env is required: dev|prod)
endif
	$(eval DB_SUBNET_GROUP := $(or $(DB_SUBNET_GROUP),$(shell $(ENV_GET) DB_SUBNET_GROUP)))
	@if [ -z "$(DB_SUBNET_GROUP)" ]; then \
		echo "❌ DB_SUBNET_GROUP is required. Run create-db-subnet-group DB_SUBNET_GROUP=<name> first."; exit 1; \
	fi
	$(eval VPC_ID := $(shell $(ENV_GET) VPC_ID))
	$(eval SG_ID := $(shell aws ec2 describe-security-groups --filters Name=vpc-id,Values=$(VPC_ID) Name=group-name,Values=default --query 'SecurityGroups[0].GroupId' --output text --region $(AWS_REGION)))
	@DB_PASS=$$(python3 -c "import secrets; print(secrets.token_urlsafe(24))"); \
	aws secretsmanager create-secret \
		--name "$(DB_NAME)-admin-password" \
		--secret-string "{\"username\":\"dbadmin\",\"password\":\"$$DB_PASS\"}" \
		--tags Key=Project,Value=$(PROJECT_TAG) \
		--region $(AWS_REGION) >/dev/null 2>&1 || \
	aws secretsmanager put-secret-value \
		--secret-id "$(DB_NAME)-admin-password" \
		--secret-string "{\"username\":\"dbadmin\",\"password\":\"$$DB_PASS\"}" \
		--region $(AWS_REGION) >/dev/null; \
	if [ "$(env)" = "dev" ]; then \
		aws rds create-db-instance \
			--db-instance-identifier $(DB_NAME) \
			--db-instance-class db.t3.micro --engine postgres \
			--allocated-storage 20 \
			--master-username dbadmin --master-user-password "$$DB_PASS" \
			--db-subnet-group-name $(DB_SUBNET_GROUP) \
			--vpc-security-group-ids $(SG_ID) \
			--no-publicly-accessible --storage-encrypted \
			--tags Key=Project,Value=$(PROJECT_TAG) Key=Environment,Value=$(env) \
			--region $(AWS_REGION); \
	else \
		aws rds create-db-instance \
			--db-instance-identifier $(DB_NAME) \
			--db-instance-class db.t3.medium --engine postgres \
			--allocated-storage 100 --storage-type gp3 --multi-az \
			--master-username dbadmin --master-user-password "$$DB_PASS" \
			--db-subnet-group-name $(DB_SUBNET_GROUP) \
			--vpc-security-group-ids $(SG_ID) \
			--no-publicly-accessible --storage-encrypted \
			--tags Key=Project,Value=$(PROJECT_TAG) Key=Environment,Value=$(env) \
			--region $(AWS_REGION); \
	fi
	@echo "✓ Created RDS: $(DB_NAME) (env=$(env), password in Secrets Manager as $(DB_NAME)-admin-password)"

##@ ElastiCache

.PHONY: create-redis
create-redis: ## Create ElastiCache Redis cluster (requires: REDIS_NAME, env=dev|prod, CACHE_SUBNET_GROUP)
ifndef REDIS_NAME
	$(error REDIS_NAME is required)
endif
ifndef env
	$(error env is required: dev|prod)
endif
	$(eval CACHE_SUBNET_GROUP := $(or $(CACHE_SUBNET_GROUP),$(shell $(ENV_GET) CACHE_SUBNET_GROUP)))
	@if [ -z "$(CACHE_SUBNET_GROUP)" ]; then \
		echo "❌ CACHE_SUBNET_GROUP is required. Run create-cache-subnet-group CACHE_SUBNET_GROUP=<name> first."; exit 1; \
	fi
	@if [ "$(env)" = "dev" ]; then \
		aws elasticache create-cache-cluster \
			--cache-cluster-id $(REDIS_NAME) \
			--engine redis \
			--cache-node-type cache.t3.micro \
			--num-cache-nodes 1 \
			--cache-subnet-group-name $(CACHE_SUBNET_GROUP) \
			--tags Key=Project,Value=$(PROJECT_TAG) Key=Environment,Value=$(env) \
			--region $(AWS_REGION); \
	else \
		aws elasticache create-replication-group \
			--replication-group-id $(REDIS_NAME) \
			--replication-group-description "$(PROJECT_TAG) Redis" \
			--engine redis \
			--cache-node-type cache.t3.medium \
			--num-node-groups 1 \
			--replicas-per-node-group 1 \
			--automatic-failover-enabled \
			--at-rest-encryption-enabled \
			--transit-encryption-enabled \
			--cache-subnet-group-name $(CACHE_SUBNET_GROUP) \
			--tags Key=Project,Value=$(PROJECT_TAG) Key=Environment,Value=$(env) \
			--region $(AWS_REGION); \
	fi
	@echo "✓ Created Redis: $(REDIS_NAME) (env=$(env))"

##@ Budgets

.PHONY: create-budget
create-budget: ## Create monthly budget with alerts (requires: BUDGET_AMOUNT, BUDGET_EMAIL)
ifndef BUDGET_AMOUNT
	$(error BUDGET_AMOUNT is required)
endif
ifndef BUDGET_EMAIL
	$(error BUDGET_EMAIL is required)
endif
	$(eval ACCOUNT_ID := $(shell aws sts get-caller-identity --query Account --output text))
	$(eval BUDGET_JSON := $(shell $(BUDGET_HELPER) budget-json --name $(PROJECT_TAG)-monthly --amount $(BUDGET_AMOUNT) --tag-key Project --tag-value $(PROJECT_TAG)))
	$(eval NOTIF_JSON := $(shell $(BUDGET_HELPER) notifications --email $(BUDGET_EMAIL)))
	@aws budgets create-budget \
		--account-id $(ACCOUNT_ID) \
		--budget '$(BUDGET_JSON)' \
		--notifications-with-subscribers '$(NOTIF_JSON)'
	@echo "✓ Created budget: $$$(BUDGET_AMOUNT)/month (alerts at 80%/100% → $(BUDGET_EMAIL))"

##@ IAM Roles & Policies

.PHONY: assign-lambda-policies
assign-lambda-policies: ## Grant Lambda role access to DynamoDB/SQS/Secrets/S3 (requires: LAMBDA_ROLE_NAME)
ifndef LAMBDA_ROLE_NAME
	$(error LAMBDA_ROLE_NAME is required)
endif
	@aws iam attach-role-policy \
		--role-name $(LAMBDA_ROLE_NAME) \
		--policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
	@aws iam attach-role-policy \
		--role-name $(LAMBDA_ROLE_NAME) \
		--policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess
	@aws iam attach-role-policy \
		--role-name $(LAMBDA_ROLE_NAME) \
		--policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
	@aws iam attach-role-policy \
		--role-name $(LAMBDA_ROLE_NAME) \
		--policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
	@echo "✓ Attached DynamoDB/SQS/Secrets/S3 policies to $(LAMBDA_ROLE_NAME)"

.PHONY: create-cicd-user
create-cicd-user: ## Create CI/CD IAM user with credentials stored in Secrets Manager (requires: CICD_USER)
ifndef CICD_USER
	$(error CICD_USER is required)
endif
	@aws iam create-user --user-name $(CICD_USER) \
		--tags Key=Project,Value=$(PROJECT_TAG) Key=Purpose,Value=CICD
	@aws iam attach-user-policy \
		--user-name $(CICD_USER) \
		--policy-arn arn:aws:iam::aws:policy/PowerUserAccess
	$(eval CREDS := $(shell aws iam create-access-key --user-name $(CICD_USER) --query 'AccessKey.[AccessKeyId,SecretAccessKey]' --output text))
	@aws secretsmanager create-secret \
		--name "cicd-$(CICD_USER)-credentials" \
		--secret-string '{"access_key":"$(word 1,$(CREDS))","secret_key":"$(word 2,$(CREDS))"}' \
		--tags Key=Project,Value=$(PROJECT_TAG) \
		--region $(AWS_REGION)
	@echo "✓ Created CI/CD user: $(CICD_USER) (credentials in Secrets Manager)"

##@ Deployment

.PHONY: deploy-web
deploy-web: ## Deploy static site to S3 + invalidate CloudFront (requires: dir=<build-folder>, BUCKET_NAME)
ifndef dir
	$(error dir is required: make deploy-web dir=./build BUCKET_NAME=x)
endif
ifndef BUCKET_NAME
	$(error BUCKET_NAME is required)
endif
	@aws s3 sync $(dir) s3://$(BUCKET_NAME) --delete --region $(AWS_REGION)
	@if grep -q CLOUDFRONT_DIST_ID .env 2>/dev/null; then \
		aws cloudfront create-invalidation \
			--distribution-id $(shell $(ENV_GET) CLOUDFRONT_DIST_ID) \
			--paths "/*"; \
		echo "✓ Deployed and invalidated CloudFront cache"; \
	else \
		echo "✓ Deployed to S3 (no CloudFront distribution found)"; \
	fi

.PHONY: backup-secrets
backup-secrets: ## Backup all secrets to .backups/secrets/
	@mkdir -p .backups/secrets
	@aws secretsmanager list-secrets \
		--query 'SecretList[].Name' --output text --region $(AWS_REGION) | \
		tr '\t' '\n' | while read name; do \
			aws secretsmanager get-secret-value \
				--secret-id "$$name" \
				--query SecretString --output text --region $(AWS_REGION) \
				> ".backups/secrets/$$name.json" 2>/dev/null || true; \
		done
	@echo "✓ Backed up secrets to .backups/secrets/"

