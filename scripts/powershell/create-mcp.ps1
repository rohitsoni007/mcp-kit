# download-mcp-servers.ps1
# Purpose: Download MCP servers and generate JSON output dynamically
# Detects HTTP (via remotes[].transport_type == "sse") and STDIO servers
$BASE_URL = "https://api.mcp.github.com"
$DATE = "2025-09-15"
$API_VERSION = "v0"
$API_PATH = "servers"
$LIMIT = 50
$API_URL = "${BASE_URL}/${DATE}/${API_VERSION}/${API_PATH}"
$serverApiUrl = "${API_URL}?limit=${LIMIT}"
$distFolder = "dist"
$outputFile = "$distFolder/mcp_servers.json"
$baseTemplateFile = "templates/base_mcp.json"

# Load base template data
Write-Host "Loading base template from $baseTemplateFile ..." -ForegroundColor Cyan
$baseData = @()
if (Test-Path $baseTemplateFile) {
    try {
        $baseData = Get-Content $baseTemplateFile -Raw | ConvertFrom-Json
        Write-Host "✅ Loaded $($baseData.Count) base servers from template" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Failed to load base template: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️ Base template file not found: $baseTemplateFile" -ForegroundColor Yellow
}

Write-Host "Fetching MCP server data from $serverApiUrl ..." -ForegroundColor Cyan

try {
    $headers = @{
        "User-Agent" = "PowerShell-MCP-Client"
        "Accept"     = "application/json"
    }

    $response = Invoke-RestMethod -Uri $serverApiUrl -Headers $headers -UseBasicParsing
} catch {
    Write-Host "❌ Failed to fetch data: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

if (-not $response) {
    Write-Host "❌ No data received from API." -ForegroundColor Red
    exit 1
}

# Handle various response shapes
if ($response.servers) {
    $servers = $response.servers
} elseif ($response.items) {
    $servers = $response.items
} elseif ($response -is [System.Collections.IEnumerable]) {
    $servers = $response
} else {
    Write-Host "⚠️ Unexpected response shape. Saving raw_response.json..." -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 10 | Out-File "raw_response.json" -Encoding UTF8
    exit 1
}

Write-Host "✅ Found $($servers.Count) servers. Processing..." -ForegroundColor Green

# Start with base template data
$formattedData = @()
if ($baseData) {
    $formattedData += $baseData
    Write-Host "✅ Added $($baseData.Count) base servers to output" -ForegroundColor Green
}

foreach ($server in $servers) {
    $name = $server.name
    $description = $server.description
    $version = $server.version
    $remotes = $server.remotes
    $mcpId = $null
    if ($server._meta -and $server._meta.'io.modelcontextprotocol.registry/official' -and $server._meta.'io.modelcontextprotocol.registry/official'.id) {
        $mcpId = $server._meta.'io.modelcontextprotocol.registry/official'.id
    }
    
    $gallery = if ($mcpId) { "${API_URL}/${mcpId}" } else { $API_URL }

    if (-not $name) { continue }

    $simpleName = ($name -split "/")[-1]
    $simpleName = ($simpleName.Substring(0,1).ToUpper() + $simpleName.Substring(1))

    # --- Detect HTTP type (via remotes[].transport_type) ---
    $isHttp = $false
    $url = $null
    $headerKeyName = $null

    if ($remotes) {
        foreach ($remote in $remotes) {
            if ($remote.transport_type) {
                $isHttp = $true
                $url = $remote.url
                foreach ($header in $remote.headers) {
                    $headerKeyName = $header.name
                    break
                }
                break
            }
        }
    }

    # --- Build MCP entry based on detected type ---
    if ($isHttp) {
        # HTTP type
        $mcpEntry = [ordered]@{
            "type" = "http"
            "url" = $url
            "gallery" = $gallery
            "version" = $version
        }
        
        # Only add headers if we have a valid header key name
        if ($headerKeyName) {
            $mcpEntry["headers"] = [ordered]@{
                $headerKeyName = "YOUR_API_KEY"
            }
        }
    }
    else {
        # STDIO type
        $identifier = $null
        $packageVersion = $null
        $runtime_hint = $null
        foreach ($package in $server.packages) {
            $identifier = $package.identifier
            $packageVersion = $package.version
            $registry_type =  $package.registry_type
            $runtime_hint = $package.runtime_hint
            if($registry_type -eq "pypi") {
                $runtime_hint = "uvx"
            }
            break
        }
        
        if ($identifier -and $packageVersion) {
            if($packageVersion -eq "latest"){
                $args = @("$identifier@$packageVersion")
            }else{
                $args = @("$identifier==$packageVersion")
            }
            
        } elseif ($identifier) {
            $args = @($identifier)
        } else {
            $args = @($identifier)
        }

        $mcpEntry = [ordered]@{
            "type" = "stdio"
            "command" = $runtime_hint
            "args" = $args
            "gallery" = $gallery
            "version" = $version
        }
    }

    # --- Build final object ---
    $mcpObject = [ordered]@{
        "name" = $simpleName
        "description" = $description
        "mcp" = [ordered]@{
            $name = $mcpEntry
        }
    }

    $formattedData += $mcpObject
}

$totalServers = $formattedData.Count
$baseServersCount = if ($baseData) { $baseData.Count } else { 0 }
$fetchedServersCount = $totalServers - $baseServersCount

if ($totalServers -eq 0) {
    Write-Host "⚠️ No servers processed. Saving raw_response.json for inspection..." -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 10 | Out-File "raw_response.json" -Encoding UTF8
    exit 1
}

# Create dist folder if it doesn't exist
if (-not (Test-Path $distFolder)) {
    New-Item -ItemType Directory -Path $distFolder -Force | Out-Null
    Write-Host "Created directory: $distFolder" -ForegroundColor Green
}

# Save final JSON
$formattedData | ConvertTo-Json -Depth 8 -Compress | Out-File -FilePath $outputFile -Encoding UTF8

Write-Host "✅ JSON file generated successfully: $outputFile" -ForegroundColor Green
Write-Host "Total servers: $totalServers (Base: $baseServersCount, Fetched: $fetchedServersCount)" -ForegroundColor Cyan
