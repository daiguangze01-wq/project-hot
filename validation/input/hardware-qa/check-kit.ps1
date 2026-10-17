# B6 QA kit completeness check (does not replace human judgement)
# Usage: & .\validation\input\hardware-qa\check-kit.ps1
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$errors = [System.Collections.Generic.List[string]]::new()

$groups = @{
  'NKRO' = 'report-nkro-*.txt'
  '6KRO' = 'report-6kro-*.txt'
  'membrane' = 'report-membrane-*.txt'
}
foreach ($name in $groups.Keys) {
  $files = @(Get-ChildItem -Path (Join-Path $dir $groups[$name]) -File -ErrorAction SilentlyContinue)
  if ($files.Count -eq 0) { $errors.Add("missing $name report file") ; continue }
  $f = $files | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($f.Length -lt 100) { $errors.Add("$($f.Name) looks empty") }
  $txt = Get-Content $f.FullName -Raw
  if ($txt -notmatch 'TASK-062|键盘|keyboard|K01') { $errors.Add("$($f.Name) does not look like a manual_test report") }
}

$template = Join-Path $dir 'REPORT-TEMPLATE.md'
if (-not (Test-Path $template)) { $errors.Add('missing REPORT-TEMPLATE.md') }
else {
  $t = Get-Content $template -Raw
  if ($t -match '\|  \|  \|  \|') { $errors.Add('REPORT-TEMPLATE.md still has empty keyboard rows') }
}

Write-Output "B6 kit: $($groups.Count) keyboard reports expected; found $((Get-ChildItem -Path (Join-Path $dir 'report-*.txt') -File -ErrorAction SilentlyContinue).Count)"
if ($errors.Count -gt 0) {
  Write-Output "INCOMPLETE ($($errors.Count)):"
  $errors | ForEach-Object { Write-Output " - $_" }
  exit 1
}
Write-Output 'OK: kit files present. Human must review the actual success counts.'
exit 0
