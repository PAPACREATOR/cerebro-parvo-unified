[CmdletBinding()]
param(
    [string]$ToolsRoot = 'C:\Nexus-Tools'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$inventoryPath = Join-Path $ToolsRoot 'external-tools-inventory.json'
if (-not (Test-Path -LiteralPath $inventoryPath)) {
    throw 'NEXUS_EXTERNAL_INVENTORY_REQUIRED'
}

$inventory = Get-Content -LiteralPath $inventoryPath -Raw | ConvertFrom-Json
if ($inventory.schema -ne 'nexus.external-inventory.v1') {
    throw 'NEXUS_EXTERNAL_INVENTORY_INVALID'
}

$catalog = [ordered]@{
    ace_step = [ordered]@{
        source = 'https://github.com/ace-step/ACE-Step-1.5.git'
        pin = 'ca1e85fe9430179831e6bc6be790c332190a3866'
        license = 'MIT'
        destination = (Join-Path $ToolsRoot 'ACE-Step-1.5')
        action = 'PROVISION_GUARDED'
    }
    forge = [ordered]@{
        source = 'https://github.com/lllyasviel/stable-diffusion-webui-forge.git'
        pin = 'dfdcbab685e57677014f05a3309b48cc87383167'
        license = 'AGPL-3.0'
        destination = (Join-Path $ToolsRoot 'Forge')
        action = 'PROVISION_GUARDED'
    }
    libreoffice = [ordered]@{
        source = 'system/external'
        pin = $null
        license = 'VERIFY_INSTALLED_PACKAGE'
        destination = $null
        action = 'VERIFY_OR_MANUAL_INSTALL'
    }
    zotero = [ordered]@{
        source = 'system/external'
        pin = $null
        license = 'VERIFY_INSTALLED_PACKAGE'
        destination = $null
        action = 'VERIFY_OR_MANUAL_INSTALL'
    }
    open_notebook = [ordered]@{
        source = 'https://github.com/lfnovo/open-notebook'
        pin = '315d5255af2a5132aada41c94d5c3c5dc8e837aa'
        license = 'VERIFY_UPSTREAM_RELEASE'
        destination = (Join-Path $ToolsRoot 'OpenNotebook')
        action = 'VERIFY_OR_PROVISION_GUARDED'
    }
    languagetool = [ordered]@{
        source = 'system/external'
        pin = $null
        license = 'VERIFY_INSTALLED_PACKAGE'
        destination = (Join-Path $ToolsRoot 'LanguageTool')
        action = 'VERIFY_OR_MANUAL_INSTALL'
    }
    ffmpeg = [ordered]@{
        source = 'system/external'
        pin = $null
        license = 'VERIFY_INSTALLED_PACKAGE'
        destination = $null
        action = 'VERIFY_OR_MANUAL_INSTALL'
    }
}

$planItems = @()
foreach ($name in $catalog.Keys) {
    $state = $inventory.items.$name
    if ($null -eq $state) { continue }
    $missing = ($state.status -like 'MISSING*')
    $planItems += [ordered]@{
        name = $name
        current_status = $state.status
        required = [bool]$missing
        source = $catalog[$name].source
        pin = $catalog[$name].pin
        license = $catalog[$name].license
        destination = $catalog[$name].destination
        action = if ($missing) { $catalog[$name].action } else { 'NONE_PRESENT' }
    }
}

$plan = [ordered]@{
    schema = 'nexus.external-provision-plan.v1'
    generated_utc = [DateTime]::UtcNow.ToString('o')
    inventory = $inventoryPath
    mode = 'PLAN_ONLY'
    execution_authorized = $false
    items = $planItems
    note = 'This file is a read-only plan. It does not download, install, start, modify ACLs, create users, or execute external provisioning.'
}

$planPath = Join-Path $ToolsRoot 'external-provision-plan.json'
$plan | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $planPath -Encoding UTF8

Write-Host 'NEXUS EXTERNAL PROVISION PLAN = PASS'
Write-Host ('PLAN: ' + $planPath)
Write-Host 'MODE: PLAN_ONLY'
