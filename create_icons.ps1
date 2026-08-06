# Opprett ikonmappe
New-Item -ItemType Directory -Force -Path "static"

# Du kan bruke online icon generator som:
# https://www.pwabuilder.com/imageGenerator
# eller
# https://realfavicongenerator.net/

Write-Host "📱 Last ned ikoner fra:"
Write-Host "1. Gå til https://www.pwabuilder.com/imageGenerator"
Write-Host "2. Last opp et 512x512 bilde (emoji eller logo)"
Write-Host "3. Last ned zip-filen"
Write-Host "4. Pakk ut alle ikoner til static/ mappen"
Write-Host ""
Write-Host "Eller bruk denne emoji som placeholder:"
Write-Host "📝 (kopier til en bildeeditor og lagre som PNG)"