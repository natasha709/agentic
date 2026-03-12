$lines = Get-Content "backend/main.py"
$totalLines = $lines.Count
$firstPart = $lines[0..432]
$lastPartStart = 463
if ($lastPartStart -lt $totalLines) {
    $lastPart = $lines[$lastPartStart..($totalLines-1)]
    $result = $firstPart + $lastPart
} else {
    $result = $firstPart
}
$result | Set-Content "backend/main_fixed.py"
Write-Host "Done! Fixed file has $(($result | Measure-Object -Line).Lines) lines"
