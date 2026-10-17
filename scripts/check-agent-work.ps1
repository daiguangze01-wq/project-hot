# check-agent-work.ps1
# 多 Agent 工作保障检查：任务唯一性、写域冲突、handoff、独立评审、依赖完整性。
# 用法：pwsh -File scripts/check-agent-work.ps1
# 退出码：0 = 通过；1 = 有 error。

[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$taskFile = Join-Path $Root 'docs/tasks.json'
if (-not (Test-Path $taskFile)) {
    Write-Error "找不到 $taskFile"
    exit 1
}

$data = Get-Content $taskFile -Raw -Encoding UTF8 | ConvertFrom-Json
$errors = [System.Collections.Generic.List[string]]::new()

function Add-Err([string]$msg) { $script:errors.Add($msg) }

# 1. 唯一 ID + 必填字段 + 状态枚举
$ids = @{}
foreach ($t in @($data.tasks)) {
    if ([string]::IsNullOrWhiteSpace($t.id)) { Add-Err "存在无 id 的任务"; continue }
    if ($ids.ContainsKey($t.id)) { Add-Err "重复 TASK ID: $($t.id)" } else { $ids[$t.id] = $true }

    foreach ($field in @('title', 'status', 'owner', 'reviewer', 'write_scope', 'depends_on', 'req', 'acceptance', 'risk')) {
        if (-not ($t.PSObject.Properties.Name -contains $field)) {
            Add-Err "$($t.id): 缺少字段 $field"
        }
    }
    if ($data.status_values -notcontains $t.status) {
        Add-Err "$($t.id): 非法状态 '$($t.status)'"
    }
    if (@($t.write_scope).Count -eq 0) {
        Add-Err "$($t.id): write_scope 为空"
    }
    if (@($t.depends_on).Count -gt 0 -and @($t.depends_on) -contains $t.id) {
        Add-Err "$($t.id): 依赖自己"
    }
}

# 2. 依赖必须存在；简单环检测（DFS）
$depMap = @{}
foreach ($t in @($data.tasks)) {
    $depMap[$t.id] = @($t.depends_on)
}
foreach ($t in @($data.tasks)) {
    foreach ($dep in @($t.depends_on)) {
        if (-not $ids.ContainsKey($dep)) { Add-Err "$($t.id): 依赖不存在 $dep" }
    }
}
$state = @{}
function Visit([string]$id) {
    if ($state[$id] -eq 'visiting') { Add-Err "依赖环: $id"; return }
    if ($state[$id] -eq 'done') { return }
    $state[$id] = 'visiting'
    foreach ($dep in @($depMap[$id])) {
        if ($depMap.ContainsKey($dep)) { Visit $dep }
    }
    $state[$id] = 'done'
}
foreach ($t in @($data.tasks)) { Visit $t.id }

# 3. done 任务必须有 handoff / 独立评审（支持任务可豁免）
foreach ($t in @($data.tasks)) {
    if ($t.status -ne 'done') { continue }

    if ($t.handoff_required -eq $true) {
        if ([string]::IsNullOrWhiteSpace($t.handoff)) {
            Add-Err "$($t.id): handoff_required=true 但 handoff 为空"
        } else {
            $p = Join-Path $Root $t.handoff
            if (-not (Test-Path $p)) { Add-Err "$($t.id): handoff 文件不存在 $($t.handoff)" }
        }
    }

    if ($t.review_required -eq $true) {
        if ([string]::IsNullOrWhiteSpace($t.review_ref)) {
            Add-Err "$($t.id): review_required=true 但 review_ref 为空"
        } else {
            $p = Join-Path $Root $t.review_ref
            if (-not (Test-Path $p)) { Add-Err "$($t.id): review 文件不存在 $($t.review_ref)" }
        }
    }
}

# 4. 活跃任务（in_progress/review）写域不得重叠
function Test-ScopeOverlap([string]$a, [string]$b) {
    $a = $a.Replace('\', '/').Trim('/')
    $b = $b.Replace('\', '/').Trim('/')
    if ($a -eq $b) { return $true }
    if ($a.StartsWith($b + '/') -or $b.StartsWith($a + '/')) { return $true }
    return $false
}

$active = @($data.tasks | Where-Object { $_.status -in @('in_progress', 'review') })
for ($i = 0; $i -lt $active.Count; $i++) {
    for ($j = $i + 1; $j -lt $active.Count; $j++) {
        $a = $active[$i]; $b = $active[$j]
        foreach ($sa in @($a.write_scope)) {
            foreach ($sb in @($b.write_scope)) {
                if (Test-ScopeOverlap $sa $sb) {
                    Add-Err "写域冲突: $($a.id) [$sa] vs $($b.id) [$sb]"
                }
            }
        }
    }
}

# 5. 汇总
$all = @($data.tasks)
$done = @($all | Where-Object { $_.status -eq 'done' }).Count
$activeCount = $active.Count
$future = @($all | Where-Object { $_.status -eq 'future' }).Count
$blocked = @($all | Where-Object { $_.status -eq 'blocked' }).Count

Write-Output "tasks=$($all.Count) done=$done active=$activeCount future=$future blocked=$blocked"

if ($errors.Count -gt 0) {
    Write-Output "--- ERRORS ($($errors.Count)) ---"
    $errors | ForEach-Object { Write-Output "ERROR: $_" }
    exit 1
}

Write-Output "OK: task ownership, handoff, review, dependencies, and active write scopes are consistent."
exit 0

