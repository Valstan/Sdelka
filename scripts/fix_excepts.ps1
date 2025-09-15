Param()

Write-Host "Running fix_excepts.ps1..."

$pattern = '(?m)except\s+Exception\s*:\r?\n([ \t]*)pass\b'

$files = Get-ChildItem -Path . -Recurse -Include *.py -File | Where-Object { $_.FullName -notmatch '\\venv\\|\\.venv\\|\\.git\\' }
$total = 0
foreach ($f in $files) {
    $text = Get-Content -Raw -Encoding UTF8 -Path $f.FullName
    $new = [regex]::Replace($text, $pattern, 'except Exception as exc:`n$1logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)')
    if ($new -ne $text) {
        Copy-Item -Path $f.FullName -Destination ($f.FullName + '.bak') -Force
        Set-Content -Path $f.FullName -Value $new -Encoding UTF8
        Write-Host "Patched $($f.FullName)"
        $total += 1
    }
}
Write-Host "Done. Files patched: $total"


