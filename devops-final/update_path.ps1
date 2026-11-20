$oldPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
# Remove any existing JDK 8 entry
$cleanPath = $oldPath -replace ';?C:\\Program Files\\Eclipse Adoptium\\jdk-8\.0\.452\.9-hotspot\\bin', ''
# Prepend the new JDK 25 bin directory
$newPath = 'C:\\Program Files\\Eclipse Adoptium\\jdk-25.0.5.8-hotspot\\bin;' + $cleanPath
# Persist for the current user
[Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
Write-Host "PATH updated for user."
