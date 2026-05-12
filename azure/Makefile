# ====================================================================
# Azure infrastructure Makefile
# See README.md for documentation and provisioning order.
# ====================================================================

# ---------- Config ----------
SHELL := /bin/bash
PY    := python3
SCRIPTS := scripts

# Load .env if present (auto-exported for az CLI)
ifneq (,$(wildcard .env))
  include .env
  export
endif

# ---------- Defaults (override via .env or CLI) ----------
RG_NAME              ?= my-resource-group
LOCATION             ?= eastus
KV_NAME              ?= my-keyvault
STORAGE_NAME         ?= my-storage-account
FUNC_NAME            ?= my-function-app
LOG_ANALYTICS_NAME   ?= my-log-analytics
APP_INSIGHTS_NAME    ?= my-app-insights
APIM_NAME            ?= my-apim
APIM_SKU             ?= Consumption
APIM_PUBLISHER_NAME  ?= MyOrg
APIM_PUBLISHER_EMAIL ?= admin@example.com
APP_REG_NAME         ?= my-api-app
VNET_NAME            ?= my-vnet
SUBNET_FUNC          ?= subnet-functions
SUBNET_PE            ?= subnet-private-endpoints
FRONTDOOR_NAME       ?= my-frontdoor
CUSTOM_DOMAIN        ?= www.example.com
BUDGET_NAME          ?= monthly-budget
BUDGET_AMOUNT        ?= 50
BUDGET_EMAIL         ?= admin@example.com
SERVICEBUS_NAME      ?= my-servicebus
COSMOS_NAME          ?= my-cosmosdb
COSMOS_DB_NAME       ?= my-database
REDIS_NAME           ?= my-redis
SQL_SERVER_NAME      ?= my-sql-server
SQL_DB_NAME          ?= my-sql-db
SQL_ADMIN_USER       ?= sqladmin
SP_NAME              ?= sp-cicd
WAF_POLICY_NAME      ?= my-waf-policy
TAGS                 ?= team=backend project=myapp

# Env matrices for storage and function app
STORAGE_SKU_dev      = Standard_LRS
STORAGE_SKU_prod     = Standard_ZRS
STORAGE_SKU_disaster = Standard_GRS
STORAGE_TIER_dev     = Hot
STORAGE_TIER_prod    = Hot
STORAGE_TIER_disaster = Cool

FUNC_RUNTIME_node    = node
FUNC_RUNTIME_dotnet  = dotnet-isolated
FUNC_RUNTIME_python  = python
FUNC_VERSION_node    = 20
FUNC_VERSION_dotnet  = 8
FUNC_VERSION_python  = 3.11

# ---------- Help ----------
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m [VAR=value ...]\n\n"} \
		/^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Resource Group
.PHONY: create-rg list-rg delete-rg
create-rg: ## Create resource group and save IDs to .env
	az group create --name $(RG_NAME) --location $(LOCATION) -o table
	@$(PY) $(SCRIPTS)/env_tool.py set \
		RG_NAME=$(RG_NAME) \
		LOCATION=$(LOCATION) \
		SUBSCRIPTION_ID=$$(az account show --query id -o tsv) \
		TENANT_ID=$$(az account show --query tenantId -o tsv)
	@echo "✅ Resource group '$(RG_NAME)' ready. IDs saved to .env."

list-rg: ## List all resource groups
	az group list -o table

delete-rg: ## Delete resource group (async)
	az group delete --name $(RG_NAME) --yes --no-wait
	@echo "🗑  Deletion initiated for '$(RG_NAME)'."

##@ Key Vault
.PHONY: create-kv delete-kv purge-kv
create-kv: ## Create Key Vault
	az keyvault create --name $(KV_NAME) --resource-group $(RG_NAME) --location $(LOCATION)
	@$(PY) $(SCRIPTS)/env_tool.py set KV_NAME=$(KV_NAME)
	@echo "✅ Key Vault '$(KV_NAME)' created."

delete-kv: ## Soft-delete Key Vault
	az keyvault delete --name $(KV_NAME) --resource-group $(RG_NAME)

purge-kv: ## Permanently purge a soft-deleted Key Vault
	az keyvault purge --name $(KV_NAME) --location $(LOCATION)

##@ Key Vault Secrets
.PHONY: add-secret-kv list-secrets-kv show-secret-kv delete-secret-kv purge-secret-kv
add-secret-kv: ## Set a secret (n=<name> v=<value>)
	az keyvault secret set --vault-name $(KV_NAME) --name "$(n)" --value "$(v)"

list-secrets-kv: ## List all secrets
	az keyvault secret list --vault-name $(KV_NAME) -o table

show-secret-kv: ## Show a secret value (n=<name>)
	az keyvault secret show --vault-name $(KV_NAME) --name $(n) --query value -o tsv

delete-secret-kv: ## Soft-delete a secret (n=<name>)
	az keyvault secret delete --vault-name $(KV_NAME) --name $(n)

purge-secret-kv: ## Purge a soft-deleted secret (n=<name>)
	az keyvault secret purge --vault-name $(KV_NAME) --name $(n)

##@ Key Vault Keys
.PHONY: add-key-kv list-keys-kv show-key-kv delete-key-kv purge-key-kv
add-key-kv: ## Create a key (n=<name>)
	az keyvault key create --vault-name $(KV_NAME) --name $(n) --protection software

list-keys-kv: ## List all keys
	az keyvault key list --vault-name $(KV_NAME) -o table

show-key-kv: ## Show key details (n=<name>)
	az keyvault key show --vault-name $(KV_NAME) --name $(n)

delete-key-kv: ## Soft-delete a key (n=<name>)
	az keyvault key delete --vault-name $(KV_NAME) --name $(n)

purge-key-kv: ## Purge a soft-deleted key (n=<name>)
	az keyvault key purge --vault-name $(KV_NAME) --name $(n)

##@ .env Backup/Restore via Key Vault
.PHONY: backup-env restore-env
backup-env: ## Upload .env contents to Key Vault as secret 'env-backup'
	az keyvault secret set --vault-name $(KV_NAME) --name env-backup --file .env >/dev/null
	@echo "✅ .env backed up to Key Vault '$(KV_NAME)'."

restore-env: ## Restore .env from Key Vault secret 'env-backup'
	@az keyvault secret show --vault-name $(KV_NAME) --name env-backup --query value -o tsv | \
		$(PY) $(SCRIPTS)/env_tool.py restore-from-stdin
	@echo "✅ .env restored from Key Vault."

##@ Storage
.PHONY: create-storage
# Usage: make create-storage env=<dev|prod|disaster> use=<web|functions|databricks> STORAGE_NAME=<name>
create-storage: ## Create storage account (env=, use=, STORAGE_NAME=)
	@if [ -z "$(env)" ] || [ -z "$(use)" ]; then \
		echo "❌ env=<dev|prod|disaster> and use=<web|functions|databricks> are required"; exit 1; \
	fi
	az storage account create \
		--name $(STORAGE_NAME) \
		--resource-group $(RG_NAME) \
		--location $(LOCATION) \
		--sku $(STORAGE_SKU_$(env)) \
		--kind StorageV2 \
		--access-tier $(STORAGE_TIER_$(env)) \
		$(if $(filter web,$(use)),--allow-blob-public-access true,) \
		$(if $(filter databricks,$(use)),--enable-hierarchical-namespace true,)
ifeq ($(use),web)
	az storage blob service-properties update \
		--account-name $(STORAGE_NAME) \
		--static-website \
		--index-document index.html \
		--404-document index.html
endif
	@$(PY) $(SCRIPTS)/env_tool.py set STORAGE_NAME=$(STORAGE_NAME)
	@echo "✅ Storage account '$(STORAGE_NAME)' created (env=$(env), use=$(use))."

##@ Function App
.PHONY: create-funcapp create-funcapp-insights
# Usage: make create-funcapp env=<dev|prod> runtime=<node|dotnet|python>
create-funcapp: ## Create Function App (env=, runtime=)
	@if [ -z "$(env)" ] || [ -z "$(runtime)" ]; then \
		echo "❌ env=<dev|prod> and runtime=<node|dotnet|python> are required"; exit 1; \
	fi
	az functionapp create \
		--name $(FUNC_NAME) \
		--resource-group $(RG_NAME) \
		--storage-account $(STORAGE_NAME) \
		--runtime $(FUNC_RUNTIME_$(runtime)) \
		--runtime-version $(FUNC_VERSION_$(runtime)) \
		--assign-identity "[system]" \
		--flexconsumption-location $(LOCATION) \
		--functions-version 4 \
		--https-only true
	@$(PY) $(SCRIPTS)/env_tool.py set \
		FUNC_NAME=$(FUNC_NAME) \
		FUNC_HOSTNAME=$$(az functionapp show --name $(FUNC_NAME) --resource-group $(RG_NAME) --query defaultHostName -o tsv) \
		FUNC_PRINCIPAL_ID=$$(az functionapp show --name $(FUNC_NAME) --resource-group $(RG_NAME) --query identity.principalId -o tsv)
	@echo "✅ Function App '$(FUNC_NAME)' created (env=$(env), runtime=$(runtime))."

create-funcapp-insights: ## Connect Function App to Application Insights
	az functionapp config appsettings set \
		--name $(FUNC_NAME) \
		--resource-group $(RG_NAME) \
		--settings "APPLICATIONINSIGHTS_CONNECTION_STRING=$(APP_INSIGHTS_CONN)"
	@echo "✅ Function App '$(FUNC_NAME)' connected to App Insights '$(APP_INSIGHTS_NAME)'."

##@ Application Insights
.PHONY: create-app-insights
create-app-insights: ## Create Log Analytics workspace + Application Insights
	az monitor log-analytics workspace create \
		--resource-group $(RG_NAME) \
		--workspace-name $(LOG_ANALYTICS_NAME) \
		--location $(LOCATION)
	@WS_ID=$$(az monitor log-analytics workspace show \
		--resource-group $(RG_NAME) \
		--workspace-name $(LOG_ANALYTICS_NAME) --query id -o tsv); \
	az monitor app-insights component create \
		--app $(APP_INSIGHTS_NAME) \
		--resource-group $(RG_NAME) \
		--location $(LOCATION) \
		--kind web \
		--application-type web \
		--workspace "$$WS_ID"
	@$(PY) $(SCRIPTS)/env_tool.py set \
		LOG_ANALYTICS_NAME=$(LOG_ANALYTICS_NAME) \
		APP_INSIGHTS_NAME=$(APP_INSIGHTS_NAME) \
		APP_INSIGHTS_KEY=$$(az monitor app-insights component show --app $(APP_INSIGHTS_NAME) --resource-group $(RG_NAME) --query instrumentationKey -o tsv) \
		APP_INSIGHTS_CONN=$$(az monitor app-insights component show --app $(APP_INSIGHTS_NAME) --resource-group $(RG_NAME) --query connectionString -o tsv)
	@echo "✅ App Insights '$(APP_INSIGHTS_NAME)' created. Keys saved to .env."

##@ Entra ID (App Registration + Roles + Groups)
.PHONY: create-app-reg create-app-roles create-api-groups assign-groups-to-roles
create-app-reg: ## Create Entra ID app registration, save client ID
	az ad app create --display-name $(APP_REG_NAME) >/dev/null
	@$(PY) $(SCRIPTS)/env_tool.py set \
		APP_REG_NAME=$(APP_REG_NAME) \
		APIM_APP_CLIENT_ID=$$(az ad app list --display-name $(APP_REG_NAME) --query '[0].appId' -o tsv)
	@# Also create the service principal so role assignments work
	@CLIENT_ID=$$(az ad app list --display-name $(APP_REG_NAME) --query '[0].appId' -o tsv); \
		az ad sp create --id "$$CLIENT_ID" >/dev/null 2>&1 || true
	@echo "✅ App registration '$(APP_REG_NAME)' created."

create-app-roles: ## Add Read/Write/Admin roles to app registration
	@$(PY) $(SCRIPTS)/app_roles.py --standard --out .tmp-app-roles.json
	az ad app update --id $(APIM_APP_CLIENT_ID) --app-roles @.tmp-app-roles.json
	@rm -f .tmp-app-roles.json
	@echo "✅ Roles API.Read, API.Write, API.Admin added to app registration."

create-api-groups: ## Create AD groups (API-Readers, API-Writers, API-Admins)
	az ad group create --display-name "API-Readers" --mail-nickname api-readers
	az ad group create --display-name "API-Writers" --mail-nickname api-writers
	az ad group create --display-name "API-Admins"  --mail-nickname api-admins
	@echo "✅ Groups API-Readers, API-Writers, API-Admins created."

assign-groups-to-roles: ## Assign AD groups to app roles
	@$(PY) $(SCRIPTS)/assign_group_roles.py \
		--client-id $(APIM_APP_CLIENT_ID) \
		--pair "API-Readers:API.Read" "API-Writers:API.Write" "API-Admins:API.Admin"

##@ API Management
.PHONY: create-apim apim-add-funcapp apim-restrict-funcapp apim-add-oauth apim-add-endpoint apim-rate-limit configure-cors create-health-probe
create-apim: ## Create APIM instance and save gateway URL
	az apim create \
		--name $(APIM_NAME) \
		--resource-group $(RG_NAME) \
		--location $(LOCATION) \
		--publisher-name "$(APIM_PUBLISHER_NAME)" \
		--publisher-email $(APIM_PUBLISHER_EMAIL) \
		--sku-name $(APIM_SKU)
	@$(PY) $(SCRIPTS)/env_tool.py set \
		APIM_NAME=$(APIM_NAME) \
		APIM_GATEWAY_URL=$$(az apim show --name $(APIM_NAME) --resource-group $(RG_NAME) --query gatewayUrl -o tsv)
	@echo "✅ APIM '$(APIM_NAME)' created. Gateway URL saved to .env."

apim-add-funcapp: ## Import Function App as API (requires swagger= URL or spec= file)
	@if [ -n "$(spec)" ]; then \
		az apim api import --resource-group $(RG_NAME) --service-name $(APIM_NAME) \
			--api-id $(FUNC_NAME) --path /$(FUNC_NAME) \
			--specification-format OpenApi --specification-path $(spec); \
	elif [ -n "$(swagger)" ]; then \
		az apim api import --resource-group $(RG_NAME) --service-name $(APIM_NAME) \
			--api-id $(FUNC_NAME) --path /$(FUNC_NAME) \
			--specification-format OpenApi --specification-url $(swagger); \
	else \
		echo "❌ Provide swagger=<url> or spec=<file.json>"; exit 1; \
	fi
	@echo "✅ Function App '$(FUNC_NAME)' added to APIM at /$(FUNC_NAME)."

apim-restrict-funcapp: ## Restrict Function App to only accept traffic from APIM
	az functionapp config access-restriction add \
		--name $(FUNC_NAME) --resource-group $(RG_NAME) \
		--priority 100 --service-tag AzureCloud \
		--description "Allow APIM only"
	az functionapp config access-restriction set \
		--name $(FUNC_NAME) --resource-group $(RG_NAME) \
		--default-action Deny
	@echo "✅ Function App '$(FUNC_NAME)' restricted to APIM traffic only."

apim-add-oauth: ## Validate JWT + require any of API.Read/Write/Admin
	@$(PY) $(SCRIPTS)/apim_policy.py oauth \
		--tenant-id $(TENANT_ID) \
		--audience $(APIM_APP_CLIENT_ID) \
		--roles API.Read API.Write API.Admin \
		--out .tmp-policy.xml
	az apim api policy set --resource-group $(RG_NAME) --service-name $(APIM_NAME) \
		--api-id $(FUNC_NAME) --value @.tmp-policy.xml --format rawxml
	@rm -f .tmp-policy.xml
	@echo "✅ APIM '$(FUNC_NAME)' requires Entra ID token with API.Read/Write/Admin."

# Usage: make apim-add-endpoint path=<api-path> role=<API.Read|API.Write|API.Admin> [method=GET]
apim-add-endpoint: ## Add endpoint with role restriction (path=, role=, [method=])
	$(eval method ?= GET)
	@if [ -z "$(path)" ] || [ -z "$(role)" ]; then \
		echo "❌ path=<api-path> and role=<API.Read|API.Write|API.Admin> are required"; exit 1; \
	fi
	az apim api operation create \
		--resource-group $(RG_NAME) --service-name $(APIM_NAME) \
		--api-id $(FUNC_NAME) --operation-id $(path) \
		--display-name "$(path)" --method $(method) --url-template "/$(path)"
	@$(PY) $(SCRIPTS)/apim_policy.py oauth-role \
		--tenant-id $(TENANT_ID) \
		--audience $(APIM_APP_CLIENT_ID) \
		--role $(role) \
		--out .tmp-policy.xml
	az apim api operation policy set \
		--resource-group $(RG_NAME) --service-name $(APIM_NAME) \
		--api-id $(FUNC_NAME) --operation-id $(path) \
		--value @.tmp-policy.xml --format rawxml
	@rm -f .tmp-policy.xml
	@echo "✅ Endpoint /$(path) added, restricted to role $(role)."

apim-rate-limit: ## Rate-limit APIM API (calls=<N> period=<seconds>)
	@if [ -z "$(calls)" ] || [ -z "$(period)" ]; then \
		echo "❌ calls=<N> and period=<seconds> are required"; exit 1; \
	fi
	@$(PY) $(SCRIPTS)/apim_policy.py rate-limit --calls $(calls) --period $(period) --out .tmp-policy.xml
	az apim api policy set --resource-group $(RG_NAME) --service-name $(APIM_NAME) \
		--api-id $(FUNC_NAME) --value @.tmp-policy.xml --format rawxml
	@rm -f .tmp-policy.xml
	@echo "✅ Rate limit set on API '$(FUNC_NAME)': $(calls) per $(period)s."

configure-cors: ## Apply CORS + JWT policy to APIM API (origin=<url>)
	@if [ -z "$(origin)" ]; then echo "❌ origin=<url> is required"; exit 1; fi
	@$(PY) $(SCRIPTS)/apim_policy.py cors \
		--origin $(origin) \
		--tenant-id $(TENANT_ID) \
		--audience $(APIM_APP_CLIENT_ID) \
		--roles API.Read API.Write API.Admin \
		--out .tmp-policy.xml
	az apim api policy set --resource-group $(RG_NAME) --service-name $(APIM_NAME) \
		--api-id $(FUNC_NAME) --value @.tmp-policy.xml --format rawxml
	@rm -f .tmp-policy.xml
	@echo "✅ CORS configured for '$(origin)'."

create-health-probe: ## Add /health endpoint to APIM
	az apim api operation create \
		--resource-group $(RG_NAME) --service-name $(APIM_NAME) \
		--api-id $(FUNC_NAME) --operation-id health \
		--display-name "Health Check" --method GET --url-template "/health"
	@echo "✅ /health endpoint added."

##@ VNet & Private Endpoints
.PHONY: create-vnet vnet-integrate-funcapp create-pe-storage create-pe-keyvault
create-vnet: ## Create VNet with subnets for functions and private endpoints
	az network vnet create \
		--name $(VNET_NAME) --resource-group $(RG_NAME) --location $(LOCATION) \
		--address-prefix 10.0.0.0/16
	az network vnet subnet create \
		--name $(SUBNET_FUNC) --resource-group $(RG_NAME) --vnet-name $(VNET_NAME) \
		--address-prefix 10.0.1.0/24 --delegations Microsoft.Web/serverFarms
	az network vnet subnet create \
		--name $(SUBNET_PE) --resource-group $(RG_NAME) --vnet-name $(VNET_NAME) \
		--address-prefix 10.0.2.0/24
	@$(PY) $(SCRIPTS)/env_tool.py set \
		VNET_NAME=$(VNET_NAME) SUBNET_FUNC=$(SUBNET_FUNC) SUBNET_PE=$(SUBNET_PE)
	@echo "✅ VNet '$(VNET_NAME)' created with subnets."

vnet-integrate-funcapp: ## Integrate Function App with VNet
	az functionapp vnet-integration add \
		--name $(FUNC_NAME) --resource-group $(RG_NAME) \
		--vnet $(VNET_NAME) --subnet $(SUBNET_FUNC)

create-pe-storage: ## Private endpoint for storage
	@SA_ID=$$(az storage account show --name $(STORAGE_NAME) --resource-group $(RG_NAME) --query id -o tsv); \
	az network private-endpoint create \
		--name pe-$(STORAGE_NAME) --resource-group $(RG_NAME) \
		--vnet-name $(VNET_NAME) --subnet $(SUBNET_PE) \
		--private-connection-resource-id "$$SA_ID" \
		--group-id blob --connection-name pec-$(STORAGE_NAME)

create-pe-keyvault: ## Private endpoint for Key Vault
	@KV_ID=$$(az keyvault show --name $(KV_NAME) --resource-group $(RG_NAME) --query id -o tsv); \
	az network private-endpoint create \
		--name pe-$(KV_NAME) --resource-group $(RG_NAME) \
		--vnet-name $(VNET_NAME) --subnet $(SUBNET_PE) \
		--private-connection-resource-id "$$KV_ID" \
		--group-id vault --connection-name pec-$(KV_NAME)

##@ Front Door / CDN
.PHONY: create-frontdoor add-custom-domain create-waf-policy
create-frontdoor: ## Create Front Door pointing at static website of storage
	az afd profile create \
		--profile-name $(FRONTDOOR_NAME) --resource-group $(RG_NAME) \
		--sku Standard_AzureFrontDoor
	az afd endpoint create \
		--endpoint-name $(FRONTDOOR_NAME)-ep --profile-name $(FRONTDOOR_NAME) \
		--resource-group $(RG_NAME)
	az afd origin-group create \
		--origin-group-name og-web --profile-name $(FRONTDOOR_NAME) \
		--resource-group $(RG_NAME) \
		--probe-request-type GET --probe-protocol Https \
		--probe-interval-in-seconds 30 --probe-path /
	@WEB_HOST=$$($(PY) $(SCRIPTS)/storage_web_endpoint.py --account $(STORAGE_NAME) --resource-group $(RG_NAME)); \
	az afd origin create \
		--origin-name origin-web --origin-group-name og-web \
		--profile-name $(FRONTDOOR_NAME) --resource-group $(RG_NAME) \
		--host-name "$$WEB_HOST" --origin-host-header "$$WEB_HOST" \
		--http-port 80 --https-port 443 --priority 1
	az afd route create \
		--route-name route-web --endpoint-name $(FRONTDOOR_NAME)-ep \
		--profile-name $(FRONTDOOR_NAME) --resource-group $(RG_NAME) \
		--origin-group og-web --supported-protocols Https \
		--https-redirect Enabled --patterns-to-match "/*"
	@$(PY) $(SCRIPTS)/env_tool.py set \
		FRONTDOOR_NAME=$(FRONTDOOR_NAME) \
		FRONTDOOR_ENDPOINT=$$(az afd endpoint show --endpoint-name $(FRONTDOOR_NAME)-ep --profile-name $(FRONTDOOR_NAME) --resource-group $(RG_NAME) --query hostName -o tsv)
	@echo "✅ Front Door '$(FRONTDOOR_NAME)' created."

add-custom-domain: ## (Optional) Add custom domain with managed TLS
	az afd custom-domain create \
		--custom-domain-name $(subst .,-,$(CUSTOM_DOMAIN)) \
		--profile-name $(FRONTDOOR_NAME) --resource-group $(RG_NAME) \
		--host-name $(CUSTOM_DOMAIN) --certificate-type ManagedCertificate
	az afd route update \
		--route-name route-web --endpoint-name $(FRONTDOOR_NAME)-ep \
		--profile-name $(FRONTDOOR_NAME) --resource-group $(RG_NAME) \
		--custom-domains $(subst .,-,$(CUSTOM_DOMAIN))
	@echo "✅ Custom domain '$(CUSTOM_DOMAIN)' configured."
	@echo "⚠️  Add CNAME: $(CUSTOM_DOMAIN) → $(FRONTDOOR_ENDPOINT)"

create-waf-policy: ## Create WAF policy (default + bot protection)
	az network front-door waf-policy create \
		--name $(WAF_POLICY_NAME) --resource-group $(RG_NAME) \
		--sku Standard_AzureFrontDoor --mode Prevention
	az network front-door waf-policy managed-rules add \
		--policy-name $(WAF_POLICY_NAME) --resource-group $(RG_NAME) \
		--type Microsoft_DefaultRuleSet --version 2.1
	az network front-door waf-policy managed-rules add \
		--policy-name $(WAF_POLICY_NAME) --resource-group $(RG_NAME) \
		--type Microsoft_BotManagerRuleSet --version 1.0
	@echo "✅ WAF policy '$(WAF_POLICY_NAME)' created."

##@ Diagnostics & Alerts
.PHONY: create-diagnostics create-budget
create-diagnostics: ## Ship APIM + Function App logs to Log Analytics
	@WS_ID=$$(az monitor log-analytics workspace show --resource-group $(RG_NAME) --workspace-name $(LOG_ANALYTICS_NAME) --query id -o tsv); \
	APIM_ID=$$(az apim show --name $(APIM_NAME) --resource-group $(RG_NAME) --query id -o tsv); \
	FUNC_ID=$$(az functionapp show --name $(FUNC_NAME) --resource-group $(RG_NAME) --query id -o tsv); \
	az monitor diagnostic-settings create --name diag-apim --resource "$$APIM_ID" --workspace "$$WS_ID" \
		--logs '[{"category":"GatewayLogs","enabled":true}]' \
		--metrics '[{"category":"AllMetrics","enabled":true}]'; \
	az monitor diagnostic-settings create --name diag-func --resource "$$FUNC_ID" --workspace "$$WS_ID" \
		--logs '[{"category":"FunctionAppLogs","enabled":true}]' \
		--metrics '[{"category":"AllMetrics","enabled":true}]'
	@echo "✅ Diagnostic settings enabled."

create-budget: ## Monthly budget with 80%/100% alerts (BUDGET_AMOUNT=, BUDGET_EMAIL=)
	@START=$$($(PY) $(SCRIPTS)/budget_helper.py start-date); \
	END=$$($(PY) $(SCRIPTS)/budget_helper.py end-date --years 1); \
	NOTIF=$$($(PY) $(SCRIPTS)/budget_helper.py notifications --email $(BUDGET_EMAIL) --thresholds 80 100); \
	az consumption budget create \
		--budget-name $(BUDGET_NAME) --amount $(BUDGET_AMOUNT) --category Cost \
		--resource-group $(RG_NAME) --time-grain Monthly \
		--start-date "$$START" --end-date "$$END" \
		--notifications "$$NOTIF"
	@echo "✅ Budget '$(BUDGET_NAME)' created: \$$$(BUDGET_AMOUNT)/month."

##@ Service Bus
.PHONY: create-servicebus create-servicebus-queue
create-servicebus: ## Create Service Bus namespace (env=dev|prod)
	@if [ -z "$(env)" ]; then echo "❌ env=<dev|prod> is required"; exit 1; fi
	az servicebus namespace create \
		--name $(SERVICEBUS_NAME) --resource-group $(RG_NAME) --location $(LOCATION) \
		--sku $(if $(filter prod,$(env)),Standard,Basic)
	@$(PY) $(SCRIPTS)/env_tool.py set \
		SERVICEBUS_NAME=$(SERVICEBUS_NAME) \
		SERVICEBUS_CONN=$$(az servicebus namespace authorization-rule keys list --namespace-name $(SERVICEBUS_NAME) --resource-group $(RG_NAME) --name RootManageSharedAccessKey --query primaryConnectionString -o tsv)

create-servicebus-queue: ## Create a queue (n=<queue-name>)
	az servicebus queue create --name $(n) --namespace-name $(SERVICEBUS_NAME) --resource-group $(RG_NAME)

##@ Cosmos DB
.PHONY: create-cosmosdb create-cosmosdb-container
create-cosmosdb: ## Create Cosmos DB account + database (env=dev|prod)
	@if [ -z "$(env)" ]; then echo "❌ env=<dev|prod> is required"; exit 1; fi
	az cosmosdb create \
		--name $(COSMOS_NAME) --resource-group $(RG_NAME) \
		--locations regionName=$(LOCATION) failoverPriority=0 \
		--default-consistency-level Session \
		--enable-free-tier $(if $(filter dev,$(env)),true,false)
	az cosmosdb sql database create \
		--account-name $(COSMOS_NAME) --resource-group $(RG_NAME) --name $(COSMOS_DB_NAME)
	@$(PY) $(SCRIPTS)/env_tool.py set \
		COSMOS_NAME=$(COSMOS_NAME) \
		COSMOS_DB_NAME=$(COSMOS_DB_NAME) \
		COSMOS_CONN=$$(az cosmosdb keys list --name $(COSMOS_NAME) --resource-group $(RG_NAME) --type connection-strings --query 'connectionStrings[0].connectionString' -o tsv)

create-cosmosdb-container: ## Create Cosmos DB container (n=<name>, pk=<partition-key>)
	az cosmosdb sql container create \
		--account-name $(COSMOS_NAME) --resource-group $(RG_NAME) \
		--database-name $(COSMOS_DB_NAME) --name $(n) --partition-key-path "/$(pk)"

##@ Redis / SQL
.PHONY: create-redis create-sql
create-redis: ## Create Redis Cache (env=dev|prod)
	@if [ -z "$(env)" ]; then echo "❌ env=<dev|prod> is required"; exit 1; fi
	az redis create \
		--name $(REDIS_NAME) --resource-group $(RG_NAME) --location $(LOCATION) \
		--sku $(if $(filter prod,$(env)),Standard,Basic) \
		--vm-size $(if $(filter prod,$(env)),c1,c0)
	@$(PY) $(SCRIPTS)/env_tool.py set \
		REDIS_NAME=$(REDIS_NAME) \
		REDIS_CONN=$$(az redis list-keys --name $(REDIS_NAME) --resource-group $(RG_NAME) --query primaryKey -o tsv)

create-sql: ## Create Azure SQL server + database (env=dev|prod)
	@if [ -z "$(env)" ]; then echo "❌ env=<dev|prod> is required"; exit 1; fi
	@PW=$$(openssl rand -base64 24); \
	az sql server create --name $(SQL_SERVER_NAME) --resource-group $(RG_NAME) --location $(LOCATION) \
		--admin-user $(SQL_ADMIN_USER) --admin-password "$$PW"; \
	az sql db create --name $(SQL_DB_NAME) --resource-group $(RG_NAME) --server $(SQL_SERVER_NAME) \
		--service-objective $(if $(filter prod,$(env)),S1,Basic); \
	az sql server firewall-rule create --server $(SQL_SERVER_NAME) --resource-group $(RG_NAME) \
		--name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0; \
	az keyvault secret set --vault-name $(KV_NAME) --name sql-admin-password --value "$$PW" >/dev/null; \
	$(PY) $(SCRIPTS)/env_tool.py set \
		SQL_SERVER_NAME=$(SQL_SERVER_NAME) \
		SQL_DB_NAME=$(SQL_DB_NAME) \
		SQL_ADMIN_USER=$(SQL_ADMIN_USER)
	@echo "✅ SQL Server/DB created. Admin password stored in Key Vault as 'sql-admin-password'."

##@ Event Grid
.PHONY: create-eventgrid-sub
create-eventgrid-sub: ## Blob events → Function App (n=<subscription-name>)
	@if [ -z "$(n)" ]; then echo "❌ n=<subscription-name> (and function name) is required"; exit 1; fi
	@SA_ID=$$(az storage account show --name $(STORAGE_NAME) --resource-group $(RG_NAME) --query id -o tsv); \
	FN_ID=$$(az functionapp show --name $(FUNC_NAME) --resource-group $(RG_NAME) --query id -o tsv); \
	az eventgrid event-subscription create \
		--name $(n) --source-resource-id "$$SA_ID" \
		--endpoint "$$FN_ID/functions/$(n)" --endpoint-type azurefunction \
		--included-event-types Microsoft.Storage.BlobCreated Microsoft.Storage.BlobDeleted

##@ Managed Identity & Service Principal
.PHONY: assign-func-roles create-sp-cicd
assign-func-roles: ## Grant Function App identity access to Storage/SB/KV/Cosmos
	@FUNC_PID=$$(az functionapp show --name $(FUNC_NAME) --resource-group $(RG_NAME) --query identity.principalId -o tsv); \
	SA_ID=$$(az storage account show --name $(STORAGE_NAME) --resource-group $(RG_NAME) --query id -o tsv); \
	SB_ID=$$(az servicebus namespace show --name $(SERVICEBUS_NAME) --resource-group $(RG_NAME) --query id -o tsv); \
	az role assignment create --assignee "$$FUNC_PID" --role "Storage Blob Data Contributor"   --scope "$$SA_ID"; \
	az role assignment create --assignee "$$FUNC_PID" --role "Azure Service Bus Data Sender"   --scope "$$SB_ID"; \
	az role assignment create --assignee "$$FUNC_PID" --role "Azure Service Bus Data Receiver" --scope "$$SB_ID"; \
	az keyvault set-policy --name $(KV_NAME) --object-id "$$FUNC_PID" --secret-permissions get list; \
	az cosmosdb sql role assignment create --account-name $(COSMOS_NAME) --resource-group $(RG_NAME) \
		--role-definition-name "Cosmos DB Built-in Data Contributor" \
		--principal-id "$$FUNC_PID" --scope "/"
	@echo "✅ Function App identity granted access to Storage/SB/KV/Cosmos."

create-sp-cicd: ## Create service principal for CI/CD deployments
	@SP_JSON=$$(az ad sp create-for-rbac --name $(SP_NAME) --role Contributor \
		--scopes /subscriptions/$(SUBSCRIPTION_ID)/resourceGroups/$(RG_NAME) -o json); \
	CLIENT_ID=$$(echo "$$SP_JSON" | $(PY) -c 'import json,sys;print(json.load(sys.stdin)["appId"])'); \
	SECRET=$$(echo "$$SP_JSON" | $(PY) -c 'import json,sys;print(json.load(sys.stdin)["password"])'); \
	az keyvault secret set --vault-name $(KV_NAME) --name sp-cicd-client-secret --value "$$SECRET" >/dev/null; \
	$(PY) $(SCRIPTS)/env_tool.py set SP_NAME=$(SP_NAME) SP_CLIENT_ID="$$CLIENT_ID"
	@echo "✅ Service principal '$(SP_NAME)' created. Client secret stored in Key Vault 'sp-cicd-client-secret'."

##@ Deployment Slots
.PHONY: create-slot swap-slot
create-slot: ## Create a deployment slot (n=<slot-name>)
	az functionapp deployment slot create --name $(FUNC_NAME) --resource-group $(RG_NAME) --slot $(n)

swap-slot: ## Swap deployment slot to production (n=<slot-name>)
	az functionapp deployment slot swap --name $(FUNC_NAME) --resource-group $(RG_NAME) \
		--slot $(n) --target-slot production

##@ Tags & Governance
.PHONY: tag-rg assign-policies
# Usage: make tag-rg env=<dev|prod|...>
tag-rg: ## Tag the resource group and all resources (env=<value>)
	@if [ -z "$(env)" ]; then echo "❌ env=<value> is required"; exit 1; fi
	az group update --name $(RG_NAME) --tags env=$(env) $(TAGS)
	@az resource list --resource-group $(RG_NAME) --query "[].id" -o tsv | while read id; do \
		az resource tag --tags env=$(env) $(TAGS) --ids "$$id"; \
	done

assign-policies: ## Assign governance policies (tags, locations, key rotation)
	@RG_ID=$$(az group show --name $(RG_NAME) --query id -o tsv); \
	TAG_POLICY=$$($(PY) $(SCRIPTS)/policy_defs.py resolve --alias required-tag-on-rg); \
	LOC_POLICY=$$($(PY) $(SCRIPTS)/policy_defs.py resolve --alias allowed-locations); \
	KV_POLICY=$$($(PY) $(SCRIPTS)/policy_defs.py resolve --alias kv-key-rotation-interval); \
	az policy assignment create --name require-env-tag --policy "$$TAG_POLICY" --scope "$$RG_ID" \
		--params '{"tagName":{"value":"env"}}'; \
	az policy assignment create --name allowed-locations --policy "$$LOC_POLICY" --scope "$$RG_ID" \
		--params '{"listOfAllowedLocations":{"value":["$(LOCATION)"]}}'; \
	az policy assignment create --name kv-key-rotation --policy "$$KV_POLICY" --scope "$$RG_ID" \
		--params '{"maximumDaysToRotate":{"value":90}}'
	@echo "✅ Policies assigned (tag, location, key rotation)."

##@ Backup & Deploy
.PHONY: create-backup-kv create-backup-storage deploy-funcapp deploy-web
create-backup-kv: ## Back up all Key Vault secrets to .backups/keyvault/
	@mkdir -p .backups/keyvault
	@az keyvault secret list --vault-name $(KV_NAME) --query '[].name' -o tsv | while read s; do \
		az keyvault secret backup --vault-name $(KV_NAME) --name "$$s" --file ".backups/keyvault/$$s.bak"; \
	done
	@echo "✅ Key Vault secrets backed up."

create-backup-storage: ## Enable blob soft delete + versioning on storage
	az storage account blob-service-properties update \
		--account-name $(STORAGE_NAME) --resource-group $(RG_NAME) \
		--enable-delete-retention true --delete-retention-days 30 \
		--enable-versioning true

deploy-funcapp: ## Deploy function code (requires Azure Functions Core Tools)
	func azure functionapp publish $(FUNC_NAME)

deploy-web: ## Deploy React build to static website (dir=<build-folder>)
	@if [ -z "$(dir)" ]; then echo "❌ dir=<build-folder> is required"; exit 1; fi
	az storage blob upload-batch \
		--account-name $(STORAGE_NAME) --destination '$$web' \
		--source $(dir) --overwrite
