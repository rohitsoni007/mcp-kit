#!/bin/bash
# create-mcp.sh
# Purpose: Download MCP servers and generate JSON output dynamically
# Detects HTTP (via remotes[].transport_type == "sse") and STDIO servers

BASE_URL="https://api.mcp.github.com"
DATE="2025-09-15"
API_VERSION="v0"
API_PATH="servers"
LIMIT=50
API_URL="${BASE_URL}/${DATE}/${API_VERSION}/${API_PATH}"
SERVER_API_URL="${API_URL}?limit=${LIMIT}"
DIST_FOLDER="dist"
OUTPUT_FILE="$DIST_FOLDER/mcp_servers.json"
BASE_TEMPLATE_FILE="templates/base_mcp.json"

# Load base template data
echo -e "\033[36mLoading base template from $BASE_TEMPLATE_FILE ...\033[0m"
base_data="[]"
base_servers_count=0

if [ -f "$BASE_TEMPLATE_FILE" ]; then
    if base_data=$(jq . "$BASE_TEMPLATE_FILE" 2>/dev/null); then
        base_servers_count=$(echo "$base_data" | jq 'length')
        echo -e "\033[32m✅ Loaded $base_servers_count base servers from template\033[0m"
        
        # Add stargazer_count to base servers
        echo -e "\033[36mFetching GitHub stars for base servers...\033[0m"
        if github_response=$(curl -s -H "User-Agent: Bash-MCP-Client" "https://api.github.com/repos/modelcontextprotocol/servers" 2>/dev/null); then
            if base_star_count=$(echo "$github_response" | jq -r '.stargazers_count // 0' 2>/dev/null); then
                # Add stargazer_count and by field to each base server that doesn't already have it
                base_data=$(echo "$base_data" | jq --argjson stars "$base_star_count" '
                    map(
                        if .stargazer_count then . 
                        else {
                            name: .name,
                            description: .description,
                            stargazer_count: $stars,
                            by: "Modelcontextprotocol",
                            mcp: .mcp
                        } end
                    )
                ')
                echo -e "\033[32m✅ Added stargazer_count ($base_star_count) to base servers\033[0m"
            else
                echo -e "\033[33m⚠️ Failed to parse GitHub stars for base servers\033[0m"
            fi
        else
            echo -e "\033[33m⚠️ Failed to fetch GitHub stars for base servers\033[0m"
        fi
    else
        echo -e "\033[33m⚠️ Failed to load base template: Invalid JSON\033[0m"
        base_data="[]"
    fi
else
    echo -e "\033[33m⚠️ Base template file not found: $BASE_TEMPLATE_FILE\033[0m"
fi

echo -e "\033[36mFetching MCP server data from $SERVER_API_URL ...\033[0m"

# Fetch data from API
response=$(curl -s -H "User-Agent: Bash-MCP-Client" -H "Accept: application/json" "$SERVER_API_URL")

if [ $? -ne 0 ] || [ -z "$response" ]; then
    echo -e "\033[31m❌ Failed to fetch data from API.\033[0m"
    exit 1
fi

# Check if response is valid JSON
if ! echo "$response" | jq . >/dev/null 2>&1; then
    echo -e "\033[31m❌ Invalid JSON response received.\033[0m"
    exit 1
fi

# Extract servers array from response
servers=$(echo "$response" | jq -r '.servers // .items // .')

if [ "$servers" = "null" ] || [ -z "$servers" ]; then
    echo -e "\033[33m⚠️ Unexpected response shape. Saving raw_response.json...\033[0m"
    echo "$response" | jq . > raw_response.json
    exit 1
fi

server_count=$(echo "$servers" | jq 'length')
echo -e "\033[32m✅ Found $server_count servers. Processing...\033[0m"

# Start with base template data
formatted_data="$base_data"
if [ "$base_servers_count" -gt 0 ]; then
    echo -e "\033[32m✅ Added $base_servers_count base servers to output\033[0m"
fi

# Process each server
for i in $(seq 0 $((server_count - 1))); do
    server=$(echo "$servers" | jq ".[$i]")
    
    name=$(echo "$server" | jq -r '.name // empty')
    description=$(echo "$server" | jq -r '.description // empty')
    version=$(echo "$server" | jq -r '.version // empty')
    remotes=$(echo "$server" | jq '.remotes // []')
    
    # Extract MCP ID if available
    mcp_id=$(echo "$server" | jq -r '._meta."io.modelcontextprotocol.registry/official".id // empty')
    
    # Extract stargazer_count from GitHub data
    stargazer_count=$(echo "$server" | jq -r '._meta."io.modelcontextprotocol.registry/publisher-provided".github.stargazer_count // empty')
    
    # Extract organization/author from server name (e.g., "microsoft/markitdown" -> "Microsoft")
    by_organization=""
    if [[ "$name" == *"/"* ]]; then
        org_name=$(echo "$name" | cut -d'/' -f1)
        # Capitalize first letter
        by_organization="$(echo "${org_name:0:1}" | tr '[:lower:]' '[:upper:]')${org_name:1}"
    fi
    
    if [ -n "$mcp_id" ]; then
        gallery="${API_URL}/${mcp_id}"
    else
        gallery="$API_URL"
    fi
    
    if [ -z "$name" ]; then
        continue
    fi
    
    # Create simple name
    simple_name=$(basename "$name")
    simple_name="$(echo "${simple_name:0:1}" | tr '[:lower:]' '[:upper:]')${simple_name:1}"
    
    # Detect HTTP type (via remotes[].transport_type)
    is_http=false
    url=""
    header_key_name=""
    
    remote_count=$(echo "$remotes" | jq 'length')
    for j in $(seq 0 $((remote_count - 1))); do
        remote=$(echo "$remotes" | jq ".[$j]")
        transport_type=$(echo "$remote" | jq -r '.transport_type // empty')
        
        if [ -n "$transport_type" ]; then
            is_http=true
            url=$(echo "$remote" | jq -r '.url // empty')
            header_key_name=$(echo "$remote" | jq -r '.headers[0].name // empty')
            break
        fi
    done
    
    # Build MCP entry based on detected type
    if [ "$is_http" = true ]; then
        # HTTP type
        mcp_entry=$(jq -n \
            --arg type "http" \
            --arg url "$url" \
            --arg gallery "$gallery" \
            --arg version "$version" \
            '{type: $type, url: $url, gallery: $gallery, version: $version}')
        
        # Add headers if we have a valid header key name
        if [ -n "$header_key_name" ]; then
            mcp_entry=$(echo "$mcp_entry" | jq --arg key "$header_key_name" '.headers = {($key): "YOUR_API_KEY"}')
        fi
    else
        # STDIO type
        packages=$(echo "$server" | jq '.packages // []')
        identifier=""
        package_version=""
        runtime_hint=""
        args_array="[]"
        
        if [ "$(echo "$packages" | jq 'length')" -gt 0 ]; then
            package=$(echo "$packages" | jq '.[0]')
            identifier=$(echo "$package" | jq -r '.identifier // empty')
            package_version=$(echo "$package" | jq -r '.version // empty')
            registry_type=$(echo "$package" | jq -r '.registry_type // empty')
            runtime_hint=$(echo "$package" | jq -r '.runtime_hint // empty')
            
            if [ "$registry_type" = "pypi" ]; then
                runtime_hint="uvx"
            fi
            
            # Process runtime_arguments if they exist
            runtime_arguments=$(echo "$package" | jq '.runtime_arguments // []')
            if [ "$(echo "$runtime_arguments" | jq 'length')" -gt 0 ]; then
                # Process each runtime argument
                for k in $(seq 0 $(($(echo "$runtime_arguments" | jq 'length') - 1))); do
                    arg=$(echo "$runtime_arguments" | jq ".[$k]")
                    arg_type=$(echo "$arg" | jq -r '.type // empty')
                    arg_name=$(echo "$arg" | jq -r '.name // empty')
                    arg_value=$(echo "$arg" | jq -r '.value // empty')
                    
                    if [ "$arg_type" = "named" ] && [ -n "$arg_name" ]; then
                        args_array=$(echo "$args_array" | jq ". += [\"$arg_name\"]")
                        if [ -n "$arg_value" ]; then
                            args_array=$(echo "$args_array" | jq ". += [\"$arg_value\"]")
                        fi
                    elif [ "$arg_type" = "positional" ] && [ -n "$arg_value" ]; then
                        args_array=$(echo "$args_array" | jq ". += [\"$arg_value\"]")
                    fi
                done
            fi
            
            # Add package identifier with version if no runtime_arguments processed it
            if [ "$(echo "$args_array" | jq 'length')" -eq 0 ]; then
                if [ -n "$identifier" ] && [ -n "$package_version" ]; then
                    if [ "$package_version" = "latest" ]; then
                        args_array=$(echo "$args_array" | jq ". += [\"$identifier@$package_version\"]")
                    else
                        args_array=$(echo "$args_array" | jq ". += [\"$identifier==$package_version\"]")
                    fi
                elif [ -n "$identifier" ]; then
                    args_array=$(echo "$args_array" | jq ". += [\"$identifier\"]")
                fi
            else
                # Add versioned package if not already in args
                versioned_package="$identifier==$package_version"
                if [ -n "$identifier" ] && [ -n "$package_version" ]; then
                    if ! echo "$args_array" | jq -e --arg pkg "$versioned_package" 'index($pkg)' >/dev/null 2>&1; then
                        args_array=$(echo "$args_array" | jq ". += [\"$versioned_package\"]")
                    fi
                fi
            fi
            
            # Process package_arguments if they exist
            package_arguments=$(echo "$package" | jq '.package_arguments // []')
            if [ "$(echo "$package_arguments" | jq 'length')" -gt 0 ]; then
                # Process each package argument
                for k in $(seq 0 $(($(echo "$package_arguments" | jq 'length') - 1))); do
                    arg=$(echo "$package_arguments" | jq ".[$k]")
                    arg_type=$(echo "$arg" | jq -r '.type // empty')
                    arg_name=$(echo "$arg" | jq -r '.name // empty')
                    arg_value=$(echo "$arg" | jq -r '.value // empty')
                    
                    if [ "$arg_type" = "named" ] && [ -n "$arg_name" ]; then
                        args_array=$(echo "$args_array" | jq ". += [\"$arg_name\"]")
                        if [ -n "$arg_value" ]; then
                            args_array=$(echo "$args_array" | jq ". += [\"$arg_value\"]")
                        fi
                    elif [ "$arg_type" = "positional" ] && [ -n "$arg_value" ]; then
                        args_array=$(echo "$args_array" | jq ". += [\"$arg_value\"]")
                    fi
                done
            fi
        fi
        
        mcp_entry=$(jq -n \
            --arg type "stdio" \
            --arg command "$runtime_hint" \
            --argjson args "$args_array" \
            --arg gallery "$gallery" \
            --arg version "$version" \
            '{type: $type, command: $command, args: $args, gallery: $gallery, version: $version}')
    fi
    
    # Build final object
    mcp_object=$(jq -n \
        --arg name "$simple_name" \
        --arg description "$description" \
        --arg server_name "$name" \
        --argjson mcp_entry "$mcp_entry" \
        '{name: $name, description: $description, mcp: {($server_name): $mcp_entry}}')
    
    # Add stargazer_count if available
    if [ -n "$stargazer_count" ] && [ "$stargazer_count" != "null" ]; then
        mcp_object=$(echo "$mcp_object" | jq --argjson stars "$stargazer_count" '.stargazer_count = $stars')
    fi
    
    # Add by organization if available
    if [ -n "$by_organization" ]; then
        mcp_object=$(echo "$mcp_object" | jq --arg by "$by_organization" '.by = $by')
    fi
    
    # Check for duplicate names and handle them
    duplicate_count=0
    temp_data=$(echo "$formatted_data" | jq -c)
    for row in $(echo "$formatted_data" | jq -r '.[] | @base64'); do
        _jq() {
            echo ${row} | base64 --decode | jq -r ${1}
        }
        existing_name=$(_jq '.name')
        if [ "$existing_name" = "$simple_name" ]; then
            duplicate_count=$((duplicate_count + 1))
        fi
    done
    
    # If it's a duplicate, modify the display name to use the MCP key for differentiation
    if [ "$duplicate_count" -gt 0 ]; then
        # Extract the organization name from the MCP key (e.g., "microsoftdocs" from "microsoftdocs/mcp")
        if [[ "$name" == *"/"* ]]; then
            org_name=$(echo "$name" | cut -d'/' -f1)
            # Capitalize first letter
            capitalized_org="$(echo "${org_name:0:1}" | tr '[:lower:]' '[:upper:]')${org_name:1}"
            mcp_object=$(echo "$mcp_object" | jq --arg new_name "$capitalized_org-$simple_name" '.name = $new_name')
        else
            mcp_object=$(echo "$mcp_object" | jq --arg new_name "$((duplicate_count + 1))-$simple_name" '.name = $new_name')
        fi
    fi
    
    # Add to formatted data array
    formatted_data=$(echo "$formatted_data" | jq ". += [$mcp_object]")
done

total_servers=$(echo "$formatted_data" | jq 'length')
fetched_servers_count=$((total_servers - base_servers_count))

if [ "$total_servers" -eq 0 ]; then
    echo -e "\033[33m⚠️ No servers processed. Saving raw_response.json for inspection...\033[0m"
    echo "$response" | jq . > raw_response.json
    exit 1
fi

# Sort servers by stargazer_count in descending order (highest stars first)
echo -e "\033[36mSorting servers by stargazer_count...\033[0m"
formatted_data=$(echo "$formatted_data" | jq 'sort_by(.stargazer_count // 0) | reverse')
echo -e "\033[32m✅ Servers sorted by popularity\033[0m"

# Create dist folder if it doesn't exist
if [ ! -d "$DIST_FOLDER" ]; then
    mkdir -p "$DIST_FOLDER"
    echo -e "\033[32mCreated directory: $DIST_FOLDER\033[0m"
fi

# Save final JSON (compact format with UTF-8 encoding)
printf '%s' "$(echo "$formatted_data" | jq -c .)" > "$OUTPUT_FILE"

echo -e "\033[32m✅ JSON file generated successfully: $OUTPUT_FILE\033[0m"
echo -e "\033[36mTotal servers: $total_servers (Base: $base_servers_count, Fetched: $fetched_servers_count)\033[0m"